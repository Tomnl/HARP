#!/usr/bin/env python
#
# import sys
# import os
# import cv2
# import SimpleITK as sitk
# from PIL import Image
# import numpy as np
# import skimage.io as io
#
#
# path_to_test_dir = 'C:\Users\james.brown\Desktop\HARP_testing\\20140430_KLF7_E14.5_16.5b_WT_XX_rec'



# img_path_list = os.listdir(path_to_test_dir)
#
# if sys.argv[1] == 'cv':
#     for impath in img_path_list:
#         img = cv2.imread(os.path.join(path_to_test_dir, impath), cv2.CV_LOAD_IMAGE_GRAYSCALE)
#     #print img.shape, img.dtype
#
# # elif sys.argv[1] == 'numpy':
# #     for impath in img_path_list:
# #         img = scipy.ndimage.imread(os.path.join(path_to_test_dir, impath))
#     #print img.shape, img.dtype
#
# elif sys.argv[1] == 'pil':
#     for impath in img_path_list:
#         img = Image.open(os.path.join(path_to_test_dir, impath))
#         ar = np.array(img)
#     #print ar.shape, ar.dtype
#
#
# elif sys.argv[1] == 'sitk':
#     for impath in img_path_list:
#         img = sitk.ReadImage(os.path.join(path_to_test_dir, impath))
#     #print img.GetSize()
#
#
# elif sys.argv[1] == 'sitk_write':
#         impath = img_path_list[0]
#         img = sitk.ReadImage(os.path.join(path_to_test_dir, impath))
#         arr = sitk.GetArrayFromImage(img)
#         for i in range(100):
#             sitk.WriteImage(img, os.path.join(path_to_test_dir, 'testout.tif'))
#
#
# elif sys.argv[1] == 'cv_write':
#         impath = img_path_list[0]
#         img = sitk.ReadImage(os.path.join(path_to_test_dir, impath))
#         arr = sitk.GetArrayFromImage(img)
#         for i in range(100):
#             cv2.imwrite(os.path.join(path_to_test_dir, 'testout.tif'), arr)
#
# elif sys.argv[1] == 'numpy_write':
#         impath = img_path_list[0]
#         img = sitk.ReadImage(os.path.join(path_to_test_dir, impath))
#         arr = sitk.GetArrayFromImage(img)
#         for i in range(100):
#             io.imsave(os.path.join(path_to_test_dir, 'testout.tif'), arr)
