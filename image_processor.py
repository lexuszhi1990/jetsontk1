import time
import cv2
import numpy as np

class ImageCalculater(object):
  """docstring for ImageCalculater"""
  def __init__(self, width, height):
    cv2.namedWindow("frame")
    cv2.namedWindow("origin_frame")
    self.frame_width = width
    self.frame_height = height

  def save_image(self, frame, path='./', prefix='opticalfb'):
    cv2.imwrite(path + prefix + time.strftime("-%Y-%m-%d-%H-%M-%S", time.localtime())  + '.png', frame)

  def custom_wait_key(self, window_name, frame, saved_frame):
    cv2.imshow(window_name, frame)
    k = cv2.waitKey(1) & 0xff
    if k == ord('s'):
        cv2.imwrite('opticalfb' + time.strftime("-%Y-%m-%d-%H-%M-%S", time.localtime())  + '.png',saved_frame)

  def conduct_translation(self, frame):
    # ret, binary_pic_after_threshold = cv2.threshold(binary_pic,127,255,cv2.THRESH_BINARY)
    # binary_pic_median_blur = cv2.medianBlur(frame, 5)
    # binary_pic_dilation = cv2.dilate(binary_pic_median_blur ,np.ones((10,10),np.uint8),iterations = 1)
    binary_pic_dilation = cv2.dilate(frame ,np.ones((5,5),np.uint8),iterations = 1)
    binary_pic_erosion = cv2.erode(binary_pic_dilation, np.ones((10,10),np.uint8),iterations = 1)
    binary_pic_median_blur = cv2.medianBlur(binary_pic_erosion, 5)
    return binary_pic_median_blur

  def display_track_image(self, rect, area, frame):
      prvs_img = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
      current_img = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
      bounding_rect_x, bounding_rect_y, bounding_rect_w, bounding_rect_h = rect

      center_point = (bounding_rect_x+bounding_rect_w/2, bounding_rect_y+bounding_rect_h/2)
      # cv2.drawContours(current_img, contours, largest_contour_index, (255,255,255), 1, 8, hierarchy)
      cv2.rectangle(current_img, (bounding_rect_x, bounding_rect_y), (bounding_rect_x+bounding_rect_w, bounding_rect_y+bounding_rect_h), (0,255,0), 1, 8, 0);
      cv2.circle(current_img, center_point, 2, (0,0,255), -1, 8, 0)
      cv2.putText(current_img, "center at (%d, %d), width: %d, height: %d, %d"%(bounding_rect_w/2, bounding_rect_h/2, bounding_rect_w, bounding_rect_h, area), (0, 10), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.5, (0,0,0), 1, 8, False)
      # self.custom_wait_key('frame', current_img, prvs_img)
      cv2.imwrite('object-image' + time.strftime("-%Y-%m-%d-%H-%M-%S", time.localtime())  + '.png',current_img)

  def calculate_optical_flow(self, prvs_gray, current_gray):
    flow = cv2.calcOpticalFlowFarneback(prvs_gray, current_gray, 0.5, 3, 15, 3, 5, 1.2, 0)
    binary_pic = np.zeros(current_gray.shape, np.uint8)

    h, w = current_gray.shape
    total_threshold=0
    for i in xrange(0,h,5):
        for j in xrange(0,w,5):
            fx, fy = flow[i, j]
            total_threshold += abs(fx) + abs(fy)
            if abs(fx) + abs(fy) > 0.4:
                binary_pic[i, j] = 255;
    # print('mean threshold is %f'%(total_threshold/(h*w)))

    binary_pic_translated = self.conduct_translation(binary_pic)
    contours, hierarchy = cv2.findContours(binary_pic_translated,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    # print('contours is %d'%(len(contours)))
    largest_area = 0
    largest_contour_index = 0
    if len(contours) > 0:
        for k in xrange(0, len(contours)):
            area = cv2.contourArea(contours[k])
            if largest_area < area:
                largest_area = area
                largest_contour_index = k

        return contours[largest_contour_index];

        # return ((bounding_rect_x, bounding_rect_y, bounding_rect_w, bounding_rect_h), largest_area)
    else:
        print("contours is not found...")
        return False

  def calculate_contour_by_frame(self, contour, frame):
    if type(contour) is bool:
      return

    area = cv2.contourArea(contour)
    rect = cv2.minAreaRect(contour)
    (vx, vy), (x, y), angle = rect

    if (area > 2000) and (abs(angle) < 4) and (float(y)/float(x) > 2):
      print('area, %d, angle: %f, x/y: %f'%(area, abs(angle), float(y)/float(x) ))
      box = np.int0(cv2.cv.BoxPoints(rect))
      cv2.drawContours(frame, [box], 0, (255,255,255), 1, 8)
      self.custom_wait_key('origin_frame', frame, frame)
      self.save_image(frame, 'pics/')

      return True
    else:
      return False


    # area = cv2.contourArea(contour)
    # if area > 1000:
    #   ellipse = cv2.fitEllipse(contour)
    #   print(ellipse)
    #   print('end cllipse')
    #   im = cv2.ellipse(frame,ellipse,(0,255,0),2)
    # self.custom_wait_key('origin_frame', frame, frame)

    # [vx,vy,x,y] = cv2.fitLine(contour, cv2.cv.CV_DIST_L2,0,0.01,0.01)
    # lefty = int((-x*vy/vx) + y)
    # righty = int(((self.frame_width-x)*vy/vx)+y)
    # img = cv2.line(frame,(self.frame_width-1,righty),(0,lefty),(0,255,0),2)
    # self.custom_wait_key('frame', frame, frame)
    # im = cv2.drawContours(im,[box],0,(0,0,255),2)

  def search_by_optical_flow(self, camera):
    ret, prvs_frame = camera.read()
    count = intervel = 2

    while(1):
      ret, current_frame = camera.read()
      current_gray = cv2.resize(current_frame,(self.frame_width, self.frame_height), interpolation=cv2.INTER_LINEAR)
      # self.custom_wait_key('origin_frame', current_gray, current_gray)
      current_gray = cv2.cvtColor(current_gray, cv2.COLOR_BGR2GRAY)
      prvs_gray = cv2.resize(prvs_frame,(self.frame_width, self.frame_height), interpolation=cv2.INTER_LINEAR)
      prvs_gray = cv2.cvtColor(prvs_gray, cv2.COLOR_BGR2GRAY)

      count = count - 1
      if count == 1:
          count = intervel

          contour = self.calculate_optical_flow(prvs_gray, current_gray)
          if self.calculate_contour_by_frame(contour, prvs_gray):
            return contour

          prvs_frame = current_frame

if __name__ == "__main__":
  pass
else:
  pass
