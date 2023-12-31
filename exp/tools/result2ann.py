from pycocotools.coco import COCO
import json
import argparse
from mmdet.core.bbox import bbox_overlaps
import torch


def check(coco, res):
    for im_id in coco.imgToAnns:
        if im_id in res.imgToAnns:
            anns = res.imgToAnns[im_id]
            for ann in anns:
                ori_ann = coco.loadAnns(ann['ann_id'])[0]

                assert ori_ann['id'] == ann['ann_id']
                for key in ['bbox', 'segmentation', 'area', ]:
                    assert key in ori_ann, ori_ann
                    assert key in ann, ann
                    assert ori_ann[key] == ann[key], f"{key}\n\t{ori_ann}\n\t{ann}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("ori_ann", help='such as data/VOC2007/voc07_trainval.json')
    parser.add_argument("det_file", help='such as exp/latest_result.json')
    parser.add_argument("save_ann", help='such as exp/rr_latest_result.json')
    args = parser.parse_args()

    coco = COCO(args.ori_ann)
    res = coco.loadRes(args.det_file)
    # iou_sum = 0
    # num_sum = 0
    iou_sum = [0] * 5
    num_sum = [0] * 5

    for im_id in coco.imgToAnns:
        if im_id in res.imgToAnns:
            anns = res.imgToAnns[im_id]
            for ann in anns:
                ori_ann = coco.loadAnns(ann['ann_id'])[0]
                assert ori_ann['id'] == ann['ann_id'], f"{ori_ann} vs {ann}"

                for key in ['image_id', 'category_id', 'iscrowd']:
                    assert ori_ann[key] == ann[key], key

                for key in ['bbox', 'segmentation', 'area', ]:
                    if key == 'bbox':
                        #                         print(torch.tensor(ori_ann[key]).unsqueeze(-1).shape)
                        ba = torch.tensor(ori_ann[key]).unsqueeze(0)
                        ba[:, 2:4] = ba[:, 0:2] + ba[:, 2:4]
                        bb = torch.tensor(ann[key]).unsqueeze(0)
                        bb[:, 2:4] = bb[:, 0:2] + bb[:, 2:4]
                        iou = bbox_overlaps(ba, bb)

                        iii = 0
                        iou_sum[iii] += iou
                        num_sum[iii] += 1
                        if iou > 0.00001:
                            iii += 1
                            iou_sum[iii] += iou
                            num_sum[iii] += 1
                            if iou > 0.1:
                                iii += 1
                                iou_sum[iii] += iou
                                num_sum[iii] += 1
                                if iou > 0.3:
                                    iii += 1
                                    iou_sum[iii] += iou
                                    num_sum[iii] += 1
                                    if iou > 0.5:
                                        iii += 1
                                        iou_sum[iii] += iou
                                        num_sum[iii] += 1

                    ori_ann[key] = ann[key]
                ## add by fei
                ori_ann['ann_weight'] = ann['score']
    # mean_iou = iou_sum / num_sum
    mean_iou = [iou_sum[ii] / num_sum[ii] for ii in range(len(iou_sum))]
    shift_ratio = [1 - num_sum[ii] / num_sum[0] for ii in range(len(iou_sum))]
    print(mean_iou, shift_ratio)

    check(coco, res)
    json.dump(coco.dataset, open(args.save_ann, 'w'))
