import matplotlib.pyplot as plt
import numpy as np
import cv2, sys, win32gui, win32ui, win32con, win32api, PIL.Image
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
# get screen shot by window name

def bw_analysis(binary_img, p=10):
    img_size = np.shape(binary_img)
    row_num = img_size[0]
    col_num = img_size[1]
    labels = -np.ones((row_num, col_num), dtype=np.int)

    label = 0
    label_sets = []
    label_sets_which = []

    # use two-pass method for label the connected area
    for i in range(row_num):
        for j in range(col_num):

            # 如果该像素点的值为1则进行接下来的判断
            if binary_img[i, j]:
                up_connect = (j and binary_img[i, j-1])
                left_connect = (i and binary_img[i-1, j])

                up_label = label+1
                left_label = label+2
                label_temp = label

                if up_connect:
                    up_label = labels[i, j-1]
                if left_connect:
                    left_label = labels[i-1, j]

                # 如果和上，左都不相连，那么此时是一个新的孤立的点
                # 因此此时会增加一个 label 用于标记
                # 同时这个 label 是一个新的 set
                # 这个 label 对应的set的编号就是 label
                if (not left_connect and not up_connect):
                    label_sets.append({label})
                    label_sets_which.append(label)
                    label += 1

                labels[i, j] = min((label_temp, up_label, left_label))

                if (up_connect and left_connect and up_label != left_label):
                    up_set = label_sets_which[up_label]
                    left_set = label_sets_which[left_label]

                    if up_set < left_set:
                        label_sets_which[left_label] = up_set
                        label_sets[up_set].add(left_label)

                    if up_set > left_set:
                        label_sets_which[up_label] = left_set
                        label_sets[left_set].add(up_label)

    # 检测 equal set 并放在相同的集合之中
    is_changed = True
    while is_changed:
        is_changed = False
        to_be_removed = []
        for k in range(len(label_sets)-1):
            set1 = label_sets[k]
            for kk in range(k+1, len(label_sets)):
                set2 = label_sets[kk]
                for item in set2:
                    if item in set1:
                        set1 = set.union(set1, set2)
                        to_be_removed.append(set2)
                        is_changed = True
                        break
            label_sets[k] = set1

        if is_changed:
            for item in to_be_removed:
                try:
                    label_sets.remove(item)
                except:
                    pass

    for set_item in label_sets:
        min_label = min(set_item)
        for label_item in set_item:
            labels[labels == label_item] = min_label

    # update label
    # 将 equal set 中的 label 都更新为最小的那个
    max_label = labels.max()+1
    ion_num = 0
    ion_info = []
    for k in range(max_label):
        label_k = labels == k
        num_label = np.sum(label_k)
        if num_label < p:
            binary_img[labels == k] = 0
        else:
            ion_num += 1
            ion_size = int(np.sqrt(num_label/np.pi))
            index = np.nonzero(label_k)
            row_mean = int(index[0].mean())
            col_mean = int(index[1].mean())
            ion_info.append((row_mean, col_mean, ion_size))

    return (binary_img, ion_num, ion_info)

hwnd_title = dict()
def getAllWindow(hwnd, mouse):
    if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
        hwnd_title.update({hwnd: win32gui.GetWindowText(hwnd)})

def getWindow(windowName = 'Andor'):
    win32gui.EnumWindows(getAllWindow, 0)
    wanted_title = -1
    for h, t in hwnd_title.items():
        if windowName in t:
            return (h,t)

    if wanted_title == -1:
        win32api.MessageBox(0, "Andor Solis is not running", "Warning",win32con.MB_ICONWARNING)
        sys.exit()

def window_capture(windowName='Andor'):
    """
    using native windows api to get capture
    It's the fastest, about ~ms per screenshot   
    """
    (win_num, win_title) = getWindow(windowName)
    # 根据窗口句柄获取窗口的设备上下文DC（Divice Context）
    hwndDC = win32gui.GetWindowDC(win_num)
    # 根据窗口的DC获取mfcDC
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    # mfcDC创建可兼容的DC
    saveDC = mfcDC.CreateCompatibleDC()
    # 创建bigmap准备保存图片
    saveBitMap = win32ui.CreateBitmap()


    # get physical monitor information
    """
    MoniterDev = win32api.EnumDisplayMonitors(None, None)
    w = MoniterDev[0][2][2]
    h = MoniterDev[0][2][3]
    """

    # but sometimes there is scaled in the real resolution
    # there it's more important to get actual resolution

    w = int(win32api.GetSystemMetrics(0)/2)
    h = win32api.GetSystemMetrics(1)
    # print w,h　　　#图片大小
    # 为bitmap开辟空间
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
    # 高度saveDC，将截图保存到saveBitmap中
    saveDC.SelectObject(saveBitMap)
    # 截取从左上角（0，0）长宽为（w，h）的图片
    saveDC.BitBlt((0, 0), (w, h), mfcDC, (0, 0), win32con.SRCCOPY)
    # saveBitMap.SaveBitmapFile(saveDC, filename)

    # ! Using fromstring is much faster then normal method
    img = np.fromstring(saveBitMap.GetBitmapBits(True), dtype = np.uint8)
    img = img.reshape((h,w,-1))
    return cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)


"""
pre method prepared for function windos_capture2()
"""
def qimage2numpy(qimage, dtype='array'):
    """Convert QImage to numpy.ndarray.  The dtype defaults to uint8
    for QImage.Format_Indexed8 or `bgra_dtype` (i.e. a record array)
    for 32bit color images.  You can pass a different dtype to use, or
    'array' to get a 3D uint8 array for color images."""
    result_shape = (qimage.height(), qimage.width())
    temp_shape = (qimage.height(),
                  int(qimage.bytesPerLine() * 8 / qimage.depth()))
    if qimage.format() in (QtGui.QImage.Format_ARGB32_Premultiplied,
                           QtGui.QImage.Format_ARGB32,
                           QtGui.QImage.Format_RGB32):
        if dtype == 'rec':
            dtype = QtGui.bgra_dtype
        elif dtype == 'array':
            dtype = np.uint8
            result_shape += (4,)
            temp_shape += (4,)
    elif qimage.format() == QtGui.QImage.Format_Indexed8:
        dtype = np.uint8
    else:
        raise ValueError("qimage2numpy only supports 32bit and 8bit images")
        # FIXME: raise error if alignment does not match

    buf = qimage.bits().asstring(qimage.byteCount())
    result = np.frombuffer(buf, dtype).reshape(temp_shape)
    if result_shape != temp_shape:
        result = result[:, :result_shape[1]]
    if qimage.format() == QtGui.QImage.Format_RGB32 and dtype == np.uint8:
        result = result[..., :3]
    result = result[:, :, ::-1] 
    return result

def rgb2gray(img):
    """
    convert rgb image to gray scale image
    """
    if len(img.shape) == 2:
        return img
    else:
        cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)

def window_capture2(windows_name = 'Andor'):
    """
    Backup Method 
    Use qt to  get screenshot
    a little slower than win32api but much more faster than other method 
    like pyautogit etc.
    """
    (win_num, win_title) = getWindow(windowName)
    hwnd = win32gui.FindWindow(None, win_title)
    app = QApplication(sys.argv)
    screen = QApplication.primaryScreen()
    img = screen.grabWindow(hwnd).toImage()
    return qimage2numpy(img)

def has_ion(plt_option = False, bw_threshold = 160, ion_area = 15, region = [200,750,200,650]):
    img = window_capture()
    img_gray = img[region[0]:region[1],region[2]:region[3]]

    img_bw = img_gray > bw_threshold
    img2, ion_num, centers = bw_analysis(img_bw, ion_area)
    
    if  (ion_num > 0 and plt_option):
        plt.imshow(img_bw)
        plt.draw()
        plt.pause(1e-17)
    else:
        """the ion is """
        if img_bw.sum()>30:
            ion_num = -1

    return ion_num

if __name__ == "__main__":
    import time
    # img = cv2.imread('ion2.jpg')
    # img = get_screenshot([1300,450,100,100])
    t1 = time.time() 
    region = [200,750,200,650]
    img = window_capture()
    img_gray = img[region[0]:region[1],region[2]:region[3]]
    # img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    t2 = time.time()
    print('Capture Time:%.4f' % (t2-t1))
    img_bw = img_gray > 160
    img2, ion_num, centers = bw_analysis(img_bw, 20)
    t3=time.time()
    
    print('Processing Time %.5fs' %(t3-t2))
    """
    for center in centers:
        row = center[0]
        col = center[1]
        radius = 2*center[2]
        img2[row-radius:row+radius+1,col-radius]=1
        img2[row-radius:row+radius+1,col+radius]=1
        img2[row-radius,col-radius:col+radius+1]=1
        img2[row+radius,col-radius:col+radius+1]=1
    """
    print('ion num:%d' % ion_num)
    print(centers)
    plt.figure()
    fig1 = plt.subplot(121)
    plt.imshow(img)

    fig2 = plt.subplot(122)
    plt.imshow(img2)

    plt.show()


