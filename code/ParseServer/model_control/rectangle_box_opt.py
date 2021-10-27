import fitz
import numpy as np


def inter_rec(locxx, locyy):
    loc1 = locxx
    loc2 = locyy
    for i in range(0, len(locxx)):
        for j in range(0, len(locxx)):
            if i != j:
                Xmax = max(loc1[i][0], locxx[j][0])
                Ymax = max(loc1[i][1], locxx[j][1])
                M = (Xmax, Ymax)
                Xmin = min(loc2[i][0], locyy[j][0])
                Ymin = min(loc2[i][1], locyy[j][1])
                N = (Xmin, Ymin)
                if M[0] < N[0] and M[1] < N[1]:  # 判断矩形是否相交
                    loc1x = (min(loc1[i][0], locxx[j][0]), min(loc1[i][1], locxx[j][1]))
                    locly = (max(loc2[i][0], locyy[j][0]), max(loc2[i][1], locyy[j][1]))
                    aa = [loc1[i], loc1[j]]
                    bb = [loc2[i], loc2[j]]
                    loc1 = [loc1x if q in aa else q for q in loc1]
                    loc2 = [locly if w in bb else w for w in loc2]
    return loc1, loc2


def merge_intersect(all_rect):
    locxx = []
    locyy = []
    new_rect = []
    for rect in all_rect:
        locxx.append((rect.x0, rect.y0))
        locyy.append((rect.x1, rect.y1))
    loc1, loc2 = inter_rec(locxx, locyy)
    for xx, yy in zip(loc1, loc2):
        r = fitz.Rect(xx[0], xx[1], yy[0], yy[1])
        if r not in new_rect:
            new_rect.append(r)
    return new_rect


def neighbor_rec(copy_rect):
    new_rects = []
    no_merge = True
    # copy_rect.append(copy_rect[-1])
    if len(copy_rect) == 2:
        i = 0
        j = 1
        # h_dis_top = np.abs(copy_rect[i].x0 - copy_rect[j].x1)
        # h_dis_bottom = np.abs(copy_rect[i].x1 - copy_rect[j].x0)
        v_dis_left = np.abs(copy_rect[i].y1 - copy_rect[j].y0)
        v_dis_right = np.abs(copy_rect[i].y0 - copy_rect[j].y1)
        min_dis = np.min([v_dis_left, v_dis_right])
        if min_dis < 30:
            x0 = min(copy_rect[i].x0, copy_rect[i].x1, copy_rect[j].x0, copy_rect[j].x1)
            y0 = min(copy_rect[i].y0, copy_rect[i].y1, copy_rect[j].y0, copy_rect[j].y1)
            x1 = max(copy_rect[i].x0, copy_rect[i].x1, copy_rect[j].x0, copy_rect[j].x1)
            y1 = max(copy_rect[i].y0, copy_rect[i].y1, copy_rect[j].y0, copy_rect[j].y1)
            copy_rect[i] = fitz.Rect(x0, y0, x1, y1)
            new_rects.append(copy_rect[i])
        no_merge = False
        return new_rects, no_merge

    for i in range(0, len(copy_rect) - 1):
        for j in range(1, len(copy_rect)):
            h_dis_top = np.abs(copy_rect[i].x0 - copy_rect[j].x1)
            h_dis_bottom = np.abs(copy_rect[i].x1 - copy_rect[j].x0)
            v_dis_left = np.abs(copy_rect[i].y1 - copy_rect[j].y0)
            v_dis_right = np.abs(copy_rect[i].y0 - copy_rect[j].y1)
            min_dis = np.min([h_dis_top, h_dis_bottom, v_dis_left, v_dis_right])
            if min_dis < 30:
                x0 = min(copy_rect[i].x0, copy_rect[i].x1, copy_rect[j].x0, copy_rect[j].x1)
                y0 = min(copy_rect[i].y0, copy_rect[i].y1, copy_rect[j].y0, copy_rect[j].y1)
                x1 = max(copy_rect[i].x0, copy_rect[i].x1, copy_rect[j].x0, copy_rect[j].x1)
                y1 = max(copy_rect[i].y0, copy_rect[i].y1, copy_rect[j].y0, copy_rect[j].y1)
                copy_rect[i] = fitz.Rect(x0, y0, x1, y1)
                no_merge = False
        # if copy_rect[i] not in new_rects:
        new_rects.append(copy_rect[i])
    new_rects = merge_intersect(new_rects)
    return new_rects, no_merge


def merge_neighbor(all_rect):
    if len(all_rect) < 2:
        return all_rect
    tmp_rect, flag = neighbor_rec(all_rect.copy())
    while not flag and len(tmp_rect) >= 2:
        print("loop", len(tmp_rect), flag)
        tmp_rect, flag = neighbor_rec(tmp_rect.copy())
    return tmp_rect
