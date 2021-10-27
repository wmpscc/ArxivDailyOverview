import layoutparser as lp
import os
import fitz
from PIL import Image
from io import BytesIO
from ParseServer.model_control.rectangle_box_opt import inter_rec, neighbor_rec
import numpy as np


def init_model():
    model = lp.Detectron2LayoutModel(
        os.path.join(os.getcwd(), 'code/ParseServer/models/PubLayNet/faster_rcnn_R_50_FPN_3x/config.yml'),
        os.path.join(os.getcwd(),
                     'code/ParseServer/models/PubLayNet/faster_rcnn_R_50_FPN_3x/model_final.pth'),
        {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"})
    return model


model = init_model()


def convert_pdf2img(pdf_path):
    doc = fitz.open(pdf_path)  # 打开pdf文件
    images = []
    zoom = 3
    for i, page in enumerate(doc):
        pix = page.getPixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.open(BytesIO(pix.getPNGData()))
        # img.save(os.path.join('./output', str(i) + '.png'))
        images.append(img)
    return images


def merge_intersect_std(blocks):
    locxx = []
    locyy = []
    new_blocks = []
    for block in blocks:
        locxx.append(block.points[0, :].tolist())
        locyy.append(block.points[2, :].tolist())
    loc1, loc2 = inter_rec(locxx, locyy)
    for xx, yy in zip(loc1, loc2):
        tmp = lp.elements.Rectangle(xx[0], xx[1], yy[0], yy[1])
        if tmp not in new_blocks:
            new_blocks.append(tmp)
    return new_blocks


def find_nearest_distance_txt_and_merge_bbox(all_text_box, table_bbox, thod=300):  # 找到表格上下的描述
    # upper在表格上面的块
    min_dis_upper = 99999
    best_upper_box = None
    # below 在表格下面的块
    min_dis_below = 99999
    best_below_box = None

    for block in all_text_box:
        bbox = fitz.Rect((block.points[0, 0], block.points[0, 1], block.points[2, 0], block.points[2, 1]))
        if bbox.y1 < table_bbox.y0:  # upper
            if np.abs(table_bbox.x0 - bbox.x0) < thod or np.abs(table_bbox.x1 - bbox.x1) < thod:  # 满足左对齐
                dis = np.abs(table_bbox.y0 - bbox.y1)
                if dis < min_dis_upper:
                    best_upper_box = bbox
                    min_dis_upper = dis
        if bbox.y0 > table_bbox.y1:  # below
            if np.abs(table_bbox.x0 - bbox.x0) < thod or np.abs(table_bbox.x1 - bbox.x1) < thod:  # 满足左对齐
                dis = np.abs(table_bbox.y1 - bbox.y0)
                if dis < min_dis_below:
                    best_below_box = bbox
                    min_dis_below = dis
    block = None
    if min_dis_below <= min_dis_upper:
        # below
        if min_dis_below > 50:
            return table_bbox
        block = fitz.Rect(min(best_below_box.x0, table_bbox.x0), min(best_below_box.y0, table_bbox.y0),
                          max(best_below_box.x1, table_bbox.x1), max(best_below_box.y1, table_bbox.y1))
    else:
        # upper
        if min_dis_upper > 50:
            return table_bbox
        block = fitz.Rect(min(best_upper_box.x0, table_bbox.x0), min(best_upper_box.y0, table_bbox.y0),
                          max(best_upper_box.x1, table_bbox.x1), max(best_upper_box.y1, table_bbox.y1))

    return block


def parse_page(img, page_num, save_dir='./output'):  # img: rgb
    layout = model.detect(img)
    print(page_num)
    # print(page_num, layout)
    # bg = lp.draw_box(img, layout,
    #                  box_width=3,
    #                  show_element_id=True)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # bg.save(os.path.join(save_dir, 'page_' + str(page_num) + '.png'))
    figure_blocks = lp.Layout([b for b in layout if b.type == 'Figure' and b.score > 0.80])
    table_blocks = lp.Layout([b for b in layout if b.type == 'Table' and b.score > 0.15])
    text_blocks = lp.Layout([b for b in layout if (b.type == 'Text' or b.type == 'Title') and b.score > 0.2])
    text_blocks = lp.Layout([b for b in text_blocks \
                             if not any(b.is_in(b_fig) for b_fig in figure_blocks)])
    figure_blocks = merge_intersect_std(figure_blocks)

    fig_and_text = []
    for block in figure_blocks:
        bbox = fitz.Rect((block.points[0, 0], block.points[0, 1], block.points[2, 0], block.points[2, 1]))
        b = find_nearest_distance_txt_and_merge_bbox(text_blocks, bbox, thod=200)
        if b is not None:
            fig_and_text.append(lp.elements.Rectangle(b.x0, b.y0, b.x1, b.y1))

    table_and_text = []
    for block in table_blocks:
        bbox = fitz.Rect((block.points[0, 0], block.points[0, 1], block.points[2, 0], block.points[2, 1]))
        b = find_nearest_distance_txt_and_merge_bbox(text_blocks, bbox, thod=200)
        if b is not None:
            table_and_text.append(lp.elements.Rectangle(b.x0, b.y0, b.x1, b.y1))

    outputs = fig_and_text + table_and_text
    pad = 30
    new_output = []
    for block in outputs:
        new_output.append(block.pad(5, 5, pad, pad))
    outputs = merge_intersect_std(new_output)

    # print("len", len(outputs))

    for i, b in enumerate(outputs):
        c = b.crop_image(np.array(img))
        t = Image.fromarray(c)
        t.save(os.path.join(save_dir, 'page_' + str(page_num) + '_' + str(i) + '.png'))


if __name__ == '__main__':
    pil_images = convert_pdf2img('../pdf/2103.03230.pdf')
    for page_num, img in enumerate(pil_images):
        parse_page(img, page_num)
    # image = cv2.imread("/home/harvey/Desktop/2021-04-25_10-47.png")
    # image = image[..., ::-1]
    # parse_page(image)
    # a = lp.elements.Rectangle(0, 0, 10, 10)
    # b = lp.elements.Rectangle(0, 0, 50, 50)
    # tmp = b.is_in(a)
    # print(tmp)
