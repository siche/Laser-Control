import time
import win32gui, win32ui, win32con, win32api
import sys
import numpy as np
import PIL
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pyautogui
import cv2

hwnd_title = dict()
def getAllWindow(hwnd, mouse):
    if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
        hwnd_title.update({hwnd: win32gui.GetWindowText(hwnd)})

def getAndorWindow():
    win32gui.EnumWindows(getAllWindow, 0)
    wanted_title = -1
    for h, t in hwnd_title.items():
        if 'Andor' in t:
            return (h,t)

    if wanted_title == -1:
        win32api.MessageBox(0, "Andor Solis is not running", "Warning",win32con.MB_ICONWARNING)
        sys.exit()
    
def window_capture():
    
    (win_num, win_title) = getAndorWindow()
    # 根据窗口句柄获取窗口的设备上下文DC（Divice Context）
    hwndDC = win32gui.GetWindowDC(win_num)
    # 根据窗口的DC获取mfcDC
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    # mfcDC创建可兼容的DC
    saveDC = mfcDC.CreateCompatibleDC()
    # 创建bigmap准备保存图片
    saveBitMap = win32ui.CreateBitmap()
    # 获取监控器信息
    """
    MoniterDev = win32api.EnumDisplayMonitors(None, None)
    w = MoniterDev[0][2][2]
    h = MoniterDev[0][2][3]
    """
    w = 960
    h = 1080
    # print w,h　　　#图片大小
    # 为bitmap开辟空间
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
    # 高度saveDC，将截图保存到saveBitmap中
    saveDC.SelectObject(saveBitMap)
    # 截取从左上角（0，0）长宽为（w，h）的图片
    saveDC.BitBlt((0, 0), (w, h), mfcDC, (0, 0), win32con.SRCCOPY)
    # saveBitMap.SaveBitmapFile(saveDC, filename)
    img = np.fromstring(saveBitMap.GetBitmapBits(True), dtype = np.uint8)
    img = img.reshape((h,w,-1))
    return cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
    """
    plt.figure()
    ax1 = plt.subplot(131)
    ax1.imshow(img)

    ax2 = plt.subplot(132)
    ax2.imshow(mpimg.imread(filename))
    """
    # pil_im = PIL.Image.frombuffer('RGB', (w, h), img, 'raw', 'BGRX', 0, 1)
    # pil_array = np.array(pil_im)
    # print(np.shape(pil_array))
    """
    ax3 = plt.subplot(133)
    ax3.imshow(pil_array)
    plt.show()
    """
def get_screenshot(region1 = [0,0,200,100]):
    img = pyautogui.screenshot(region = region1)
    # img = cv2.cvtColor(np.asarray(img),cv2.COLOR_RGB2BGR)
    return np.asarray(img)
    

if __name__ == "__main__":
    beg = time.time()
    for i in range(10):
        b = window_capture("haha.bmp")
    end = time.time()

    for i in range(10):
        a = get_screenshot()
    end2 = time.time()

    print(end - beg)
    print(end2-end)
    print(np.shape(b))
    plt.figure()
    ax1 = plt.subplot(121)
    ax1.imshow(a)

    ax2 = plt.subplot(122)
    ax2.imshow(b)
    plt.show()
