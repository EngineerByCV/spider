# -*- coding: utf-8 -*-

import json
import re
import os
import cv2
import time
import random
import logging
import requests
from pymysql import *
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver import ActionChains

# import ctypes
#
# try:
#     temp=ctypes.windll.LoadLibrary('opencv_ffmpeg400.dll')
# except:
#     pass

# 添加debug日志
LOG_FORMAT = '%(asctime)s %(filename)s %(message)s'
logging.basicConfig(filename='get_cookies_logging.txt', level=logging.DEBUG, format=LOG_FORMAT)


class GetMess(object):
    def __init__(self, qq, pw):
        self.s = 1
        self.qq = qq
        self.pw = pw
        self.time = time.time()
        self.cookie = ''
        self.bkn = ''
        self.driver = None

    # 调用chrome得到界面
    def chrome(self):
        try:
            opt = webdriver.ChromeOptions()

            # 把chrome设置成无界面模式，不论windows还是linux都可以，自动适配对应参数
            opt.set_headless()

            driver = webdriver.Chrome(executable_path=".\chromedriver.exe", options=opt)
            # 设置浏览器窗口的位置和大小

            driver.set_window_position(0, 0)
            driver.set_window_size(1365, 938)
            driver.implicitly_wait(10)

            start_url = "https://aq.qq.com/cn2/index"
            driver.delete_all_cookies()
            driver.get(start_url)
            time.sleep(3)

            driver.find_element_by_xpath('//*[@id="banner"]/div[1]/div[1]/div/div[2]/div[2]/a').click()
            time.sleep(1)

            # 切换到登录框
            driver.switch_to.frame('embed_login_frame')

            # 输入账号
            for i in self.qq:
                time.sleep(int(i) / 10)
                driver.find_element_by_xpath('//*[@id="u"]').send_keys(i)

            # 输入密码
            for i in self.pw:
                time.sleep(random.uniform(0.3, 0.5))
                driver.find_element_by_xpath('//*[@id="p"]').send_keys(i)
            time.sleep(2)

            # 点击登录
            driver.find_element_by_xpath('//*[@id="loginform"]/div[4]/a').click()
            time.sleep(2)
            print("打开浏览器正常")
            return driver
        except:
            logging.info("浏览器打开失败")
            try:
                driver.close()
            except:
                pass

    # 对滑块的判断，并取出滑块的top
    def get_slide_block(self, driver):
        s = driver.find_element_by_xpath('//*[@id="newVcodeIframe"]/iframe')

        driver.switch_to.frame(s)

        while True:
            # 获取滑块图片的下载地址
            a = driver.find_element_by_id('slideBlock')

            image2 = a.get_attribute('src')

            css_str = driver.find_element_by_id('slideBlock').get_attribute("style")

            css_list = css_str.split(";")

            # 获取滑块的top值

            start_top = re.search(r"[0-9]{2}", css_list[2]).group()

            start_top = int(start_top)
            start_top += 9
            start_top = start_top * 2
            start_top += 20

            # print("image1:", image1)
            image1_name = 'demo1.png'  # 滑块图片名

            # 下载滑块图片并存储到本地
            target_img = Image.open(BytesIO(requests.get(image2).content))
            target_img.save(image1_name)

            # 获取图片，并灰化
            block = cv2.imread(image1_name, 0)

            # 二值化之后的图片名称
            block_name = 'demo.jpg'

            cv2.imwrite(block_name, block)

            img = Image.open("demo.jpg")

            img_array = img.load()

            top = 0
            left = 0
            right = 0
            bottom = 0

            for i in range(23, 111):
                top += img_array[i, 23]
            for i in range(23, 111):
                left += img_array[23, i]
            for i in range(23, 111):
                right += img_array[111, i]
            for i in range(23, 111):
                bottom += img_array[i, 111]
            rgb_list = [top, left, right, bottom]
            if left != max(rgb_list):
                a = driver.find_elements_by_id('e_reload')
                time.sleep(random.randint(2, 4))
                a[0].click()
                time.sleep(1)
            else:
                print("获取滑块高度正常...")
                return start_top

    # 对背景图的分析，确定需要移动的距离
    def get_slide_bkg(self, start_top, driver):
        # 获取背景大图图片的下载地址
        image2 = driver.find_element_by_id('slideBg').get_attribute('src')

        # print("image2:", image2)

        image2_name = 'demo2.png'  # 背景大图名

        # 下载滑块图片并存储到本地
        target_img = Image.open(BytesIO(requests.get(image2).content))
        target_img.save(image2_name)

        # 获取图片，并灰化
        block = cv2.imread(image2_name, 0)

        # 二值化之后的图片名称
        block_name = 'demo2.jpg'

        cv2.imwrite(block_name, block)

        img = Image.open("demo2.jpg")

        img_array = img.load()

        rgb_list = []

        for i in range(0, 680):
            left = 0
            for j in range(start_top, start_top + 90):
                left += img_array[i, j]
            rgb_list.append(left)

        for i in range(len(rgb_list) - 1):
            if rgb_list[i] - rgb_list[i + 1] > 10000:
                dis = ((i + 1) / 2.4) - 31
                print("获取移动距离正常...")
                print(int(dis))
                return int(dis)

    # 获取移动参数
    def get_track(self, distance):
        track = []
        res = 0
        current = 0
        mid = distance * 4 / 5
        t = 0.2
        v = 0
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        print("获取移动参数正常...")
        return track

    # 移动滑块，完成验证
    def let_slide_block_move(self, start_top, driver):
        button = driver.find_element_by_xpath('//*[@id="tcaptcha_drag_button"]')
        dis = self.get_slide_bkg(start_top, driver)
        track = self.get_track(dis)
        # time.sleep(random.randint(1, 3))

        # 移动滑块
        action = ActionChains(driver)
        action.click_and_hold(button).perform()
        action.reset_actions()  # 清除之前的action
        t = 0
        for i in track:
            if len(track) - t < 5:
                time.sleep(random.randint(500, 600) / 1000)
            action.move_by_offset(xoffset=i, yoffset=0).perform()
            action = ActionChains(driver)
            t += 1
        imitate = ActionChains(driver).move_by_offset(xoffset=-1, yoffset=0)
        time.sleep(random.uniform(0.001, 0.007))
        imitate.perform()
        time.sleep(random.randint(6, 10) / 10)
        imitate.perform()
        time.sleep(random.uniform(0.001, 0.009))
        imitate.perform()
        time.sleep(random.uniform(0.001, 0.006))
        imitate.perform()
        time.sleep(random.uniform(0.001, 0.005))
        imitate.perform()
        time.sleep(random.uniform(0.01, 0.02))
        ActionChains(driver).move_by_offset(xoffset=1, yoffset=0).perform()

        # 放开圆球
        time.sleep(3)
        action.release().perform()
        time.sleep(random.randint(1, 3))
        # 点击确定

        print("拖动正常...")
        return driver

    def judge_login_status(self, driver):
        status = driver.find_element_by_xpath('//*[@id="err_m"]').text
        if "不正确" in status:
            print(status)
            with open("./pw", 'r', encoding="utf-8") as f:
                pw_str = f.read()
            pw_dict = json.loads(pw_str)
            conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
                           password=pw_dict["password"],
                           charset='utf8')
            # 获得Cursor对象
            cs1 = conn.cursor()
            cs1.execute("update qq_status set status=5 where qq_num='{}';".format(self.qq))
            conn.commit()
            conn.close()
            return False
        elif "扫描" in status:
            print(status)
            with open("./pw", 'r', encoding="utf-8") as f:
                pw_str = f.read()
            pw_dict = json.loads(pw_str)
            conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
                           password=pw_dict["password"],
                           charset='utf8')
            # 获得Cursor对象
            cs1 = conn.cursor()
            cs1.execute("update qq_status set status=6 where qq_num='{}';".format(self.qq))
            conn.commit()
            conn.close()
            return False
        return True

    def change_status(self, status):
        with open("./pw", 'r', encoding="utf-8") as f:
            pw_str = f.read()
        pw_dict = json.loads(pw_str)
        conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
                       password=pw_dict["password"],
                       charset='utf8')
        # 获得Cursor对象
        cs1 = conn.cursor()
        # 修改QQ采集状态
        cs1.execute("update qq_status set status={} where qq_num='{}';".format(status, self.qq))
        conn.commit()
        try:
            conn.close()
        except:
            pass

    # 获取cookie
    def get_cookie(self, driver):
        time.sleep(3)
        qq_url = 'http://find.qq.com/#'
        # time.sleep(3)
        driver.get(qq_url)
        c_list = driver.get_cookies()
        cookie = ''
        s = ''
        for i in c_list:
            if i["name"] == "skey":
                s = i["value"]
            if cookie == '':
                cookie += i["name"] + "=" + i["value"]
            else:
                cookie += "; " + i["name"] + "=" + i["value"]
        # 生成bkn
        hash = 5381
        for i in s:
            hash += (hash << 5) + ord(i)
        bkn = hash & 2147483647

        self.cookie = cookie
        self.bkn = bkn
        with open("./pw", 'r', encoding="utf-8") as f:
            pw_str = f.read()
        pw_dict = json.loads(pw_str)
        conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
                       password=pw_dict["password"],
                       charset='utf8')
        # 获得Cursor对象
        cs1 = conn.cursor()

        ccc = cs1.execute("SELECT count FROM cookies GROUP BY count desc;")

        if ccc != 0:
            cookie_count = cs1.fetchall()[0][0]
            cs1.execute("insert into cookies values(0, '{}','{}','{}',{}, {})".format(self.qq, self.cookie, self.bkn, int(time.time()), cookie_count))

            # 修改QQ采集状态
            cs1.execute("update qq_status set status=1 where qq_num='{}';".format(self.qq))
            conn.commit()
        else:
            cs1.execute("insert into cookies values(0, '{}','{}','{}',{}, {})".format(self.qq, self.cookie, self.bkn, int(time.time()), 0))
            conn.commit()

        # time.sleep(random.randint(30, 45))
        try:
            conn.close()
        except:
            pass
        driver.close()

    def qq_count(self):
        with open("./pw", 'r', encoding="utf-8") as f:
            pw_str = f.read()
        pw_dict = json.loads(pw_str)
        conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
                       password=pw_dict["password"],
                       charset='utf8')
        # 获得Cursor对象
        cs1 = conn.cursor()
        cs1.execute("select count from qq_status where `qq_num`={};".format(self.qq))
        qq_count = cs1.fetchone()[0]
        cs1.execute("update qq_status set count={} where `qq_num`={};".format(qq_count + 1, self.qq))
        conn.commit()

        # 检查ip

    def check_ip(self):
        while True:
            # 获取ip判断，是否在可用区间
            heads = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
                "Host": "www.ip138.com"}
            try:
                res_ip = requests.get("http://2018.ip138.com/ic.asp")
                res_str = res_ip.content.decode("gbk")
                s1 = res_str.replace("\n", "")
                ip_data = s1[-24:-59:-1][::-1]
                ip = re.search(r"\[(.*)\]", ip_data).group(1)
                if "绍兴" in ip_data:
                    print("ip地址区间符合要求")
                    break
                else:
                    print("ip不符合要求，切换ip")
                    time.sleep(1)
                    # self.change_ip()
            except:
                print("获取ip失败")
                time.sleep(1)
                # self.change_ip()

    # 切换ip
    def change_ip(self):
        print("切换ip中")
        while True:
            try:
                res = os.system("rasdial 宽带连接 /disconnect")
                # import serial
                # import time
                # # 打开串口
                # serialPort = "COM11"  # 串口
                # baudRate = 9600  # 波特率
                # ser = serial.Serial(serialPort, baudRate, timeout=0.5)

                # 收发数据

                # str = "AT+CFUN=0\r"
                # ser.write((str).encode())
                # time.sleep(3)
                # str1 = "AT+CFUN=1\r"
                # ser.write((str1).encode())
                # time.sleep(3)
                # str2 = "AT\r"
                # ser.write((str2).encode())
                # print("切换ip成功")
                # 修改计算机名名字
                a = "QWERTYUIOIPASDFGHJKLZXCVBNM"
                b = "0123456789"
                str = ''
                for i in range(3):
                    str += a[random.randint(0, len(a) - 1)]
                str += '-'
                for i in range(6):
                    str += b[random.randint(0, len(b) - 1)]
                os.system(r"C:\Users\Administrator\Desktop\cs.bat, {}".format(str))
                # time.sleep(random.randint(21, 25))
                res1 = os.system("rasdial 宽带连接 057523312717 464074")
                # time.sleep(3)
                if res == 0 and res1 == 0:
                    break
            except:
                print("--->切换ip失败<---")

    def run(self):
        while True:
            try:
                requests.get("https://aq.qq.com/v2/uv_aq/html/reset_pwd/pc_reset_pwd_input_account.html?v=4.0", timeout=5)
            except:
                logging.info("网络连接超时")
                print("网络连接超时")
                continue
            # try:
            #     self.check_ip()
            # except:
            #     logging.info("切换ip失败")
            #     print("切换ip失败，new start")
            #     continue
            driver = self.chrome()
            status = None
            try:
                status = self.judge_login_status(driver)
            except Exception as e:
                print("判断扫码：%s" % e)
            if status:
                try:
                    start_top = self.get_slide_block(driver)
                    driver = self.let_slide_block_move(start_top, driver)
                    logging.info("验证成功")
                    print("验证成功")
                except:
                    self.qq_count()
                    logging.info("验证失败")
                    print("验证失败")
                    self.change_status(2)
                    try:
                        driver.close()
                    except:
                        pass
                    break
                try:
                    # 切换到登录框
                    driver.switch_to.frame('embed_login_frame')
                    status = self.judge_login_status(driver)
                except Exception as e:
                    print("判断密码错误：%s" % e)
                if status:
                    try:
                        time.sleep(3)
                        driver.switch_to.default_content()
                        a = driver.find_element_by_xpath('//*[@id="app"]/div[3]/div/div[1]/div/p[2]').text
                        logging.info("登陆成功")
                        print("登陆成功")
                    except:
                        self.qq_count()
                        logging.info("登陆失败")
                        print("登陆失败")
                        self.change_status(2)
                        self.s = 0
                        try:
                            driver.close()
                        except:
                            pass
                        break
                    try:
                        self.driver = self.get_cookie(driver)
                        self.change_status(1)
                        print("获取cookie成功")
                    except:
                        logging.info("获取cookie失败")
                        print("获取cookie失败")
                        self.change_status(2)
                        self.s = 0
                        try:
                            driver.close()
                        except:
                            pass
                    try:
                        driver.close()
                    except:
                        pass
                    break
                else:
                    print("密码错误")
                    try:
                        driver.close()
                    except:
                        pass
                    break
            else:
                print("需要扫码登录")
                try:
                    driver.close()
                except:
                    pass
                break


def main():
    while True:
        try:
            with open("./pw", 'r', encoding="utf-8") as f:
                pw_str = f.read()
            pw_dict = json.loads(pw_str)
            change_count = pw_dict["change_count"]
            conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
                           password=pw_dict["password"],
                           charset='utf8')
            # 获得Cursor对象
            cs1 = conn.cursor()
            cs1.execute("select qq_num,qq_pw from qq_status where status=0 or status=2 or status=3 or status=5 or status=6;")
            nums = cs1.fetchall()
            for num in nums:
                count = cs1.execute("select * from cookies where qq={}".format(num[0]))
                if count == 0:
                    g = GetMess(num[0], num[1])
                    logging.info("QQ: %s 获取cookie中" % num[0])
                    print("QQ: %s 获取cookie中" % num[0])
                    g.run()
                    logging.info("登录下一个qq")
                    print("   ")
            logging.info("号码登录完毕，等待循环")
            # print("号码登录完毕，等待循环")
            # time.sleep(600)
            conn.close()
        except Exception as e:
            logging.info("号码循环异常: %s" % e)
            print("号码循环异常，等待循环")

            # # 修改QQ采集状态
            # with open("./pw", 'r', encoding="utf-8") as f:
            #     pw_str = f.read()
            # pw_dict = json.loads(pw_str)
            # conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
            #                password=pw_dict["password"],
            #                charset='utf8')
            # # 获得Cursor对象
            # cs1 = conn.cursor()
            # fail = cs1.execute("select qq_num from qq_status where count>=3;")
            # if fail != 0:
            #     for qq_num in cs1.fetchall()[0]:
            #         cs1.execute("update qq_status set status=4 where qq_num='{}';".format(qq_num[0]))
            #         conn.commit()
            # conn.close()


if __name__ == '__main__':
    main()
    print("   ")
