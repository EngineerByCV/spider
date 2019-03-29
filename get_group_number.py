import copy
import os
import sys
import time
import json
import random
import logging
import requests
from pymysql import *

# 添加debug日志
LOG_FORMAT = '%(asctime)s %(filename)s %(message)s'
logging.basicConfig(filename='get_group_number_logging.txt', level=logging.DEBUG, format=LOG_FORMAT)


def up_data_to_c(up_data_d):
    with open("./pw", 'r', encoding="utf-8") as f:
        pw_str = f.read()
    pw_dict = json.loads(pw_str)
    up_statue = pw_dict["up_statue"]
    if up_statue == 1:
        up_url = pw_dict["up_url"]
        up_data = json.dumps(up_data_d)
        res = requests.post(up_url, data=up_data)
        time.sleep(random.uniform(1, 3))
        logging.info("上报 %s 返回：%s" % (len(up_data_d), res.content))
        print("上报 %s 返回：%s" % (len(up_data_d), res.content))


# 更新关键字数据表内容
def update(k, c):
    # 获取数据
    with open("./pw", 'r', encoding="utf-8") as f:
        pw_str = f.read()
    pw_dict = json.loads(pw_str)
    conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
                   password=pw_dict["password"],
                   charset='utf8')
    # 获得Cursor对象
    cs1 = conn.cursor()
    all_group_count = cs1.execute("select * from qq_qun where `key`='{}';".format(k))
    useful_group_count = cs1.execute("select * from qq_qun where count>=50 and `key`='{}';".format(k))
    cs1.execute("select sucessful_group_count from vc_keyword where `key` ='{}'".format(k))
    sucessful_group_count = cs1.fetchone()[0]
    repeat_group_count = useful_group_count - sucessful_group_count

    cs1.execute("update vc_keyword set all_group_count={},useful_group_count={},repeat_group_count={} where `key` ='{}'".format(all_group_count,useful_group_count, repeat_group_count, k))
    conn.commit()
    try:
        conn.close()
    except:
        pass


def change_ip():
    print("切换ip中")
    while True:
        try:
            with open("./pw", 'r', encoding="utf-8") as f:
                pw_str = f.read()
            pw_dict = json.loads(pw_str)
            zh = pw_dict["zh"]
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
            res1 = os.system("rasdial 宽带连接 {} 464074".format(zh))
            # time.sleep(3)
            if res == 0 and res1 == 0:
                print("连接成功")
                break
            else:
                print("连接失败")
                time.sleep(3)
        except:
            print("--->切换ip失败<---")


def main():
    while True:
        logging.info("开始新一轮循环")
        try:
            # 获取数据
            with open("./pw", 'r', encoding="utf-8") as f:
                pw_str = f.read()
            pw_dict = json.loads(pw_str)
            wait_time = pw_dict["wait_time"]
            conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
                           password=pw_dict["password"],
                           charset='utf8')
            # 获得Cursor对象
            cs1 = conn.cursor()
            conn.ping(reconnect=True)
            cs1.execute('SELECT * from vc_keyword where is_active=1')
            k_t = cs1.fetchall()

            # 构建关键字列表
            k_list = []
            for i in k_t:
                k_list.append(i[1])
                break

            # # 构建城市列表
            conn.ping(reconnect=True)
            cs1.execute("select num from city where is_active=1;")
            city_list_n = []
            for city_num in cs1.fetchall():
                city_list_n.append(city_num[0])

            # 上报数据
            up_data_d = {}

            # 遍历关键字列表
            for k in k_list:
                cs1.execute("UPDATE vc_keyword SET is_active=0 WHERE `key`='{}';".format(k))
                conn.commit()
                change_k = 0
                # 关键字失败次数
                k_count = 0

                # cs1.execute("select is_active from vc_keyword where `key`='{}'".format(k))
                # is_active = cs1.fetchone()[0]

                # 遍历城市列表
                for j in city_list_n:
                    logging.info("采集第 %s 个城市" % city_list_n.index(j))
                    print("采集第 %s 个城市" % city_list_n.index(j))

                    # 城市失败次数
                    j_count = 0
                    conn.ping(reconnect=True)

                    cs1.execute("select cookie,bkn,time from cookies")
                    cookies = cs1.fetchall()

                    # 判断关键字失败次数
                    if k_count < 2000:
                        # if len(cookies) == 0:
                        #     logging.info("无可用cookie")
                        #     print("无可用cookie")
                        #     time.sleep(300)
                        #     try:
                        #         conn.close()
                        #     except:
                        #         pass
                        #     python = sys.executable
                        #     os.execl(python, python, *sys.argv)
                        #     logging.info("重启脚本")
                        #     time.sleep(300)

                        # 选用使用次数少的qq号采集
                        for p in range(2):
                            while True:
                                conn.ping(reconnect=True)
                                counts = cs1.execute("SELECT count FROM cookies order by count;")
                                cookie_count = cs1.fetchall()[0][0]
                                if counts < 3:
                                    print("cookie数量过少")
                                    time.sleep(20)
                                    conn.close()
                                    continue
                                cs1.execute(
                                    "SELECT cookie,bkn,time FROM cookies where count={};".format(cookie_count))
                                cookie = cs1.fetchall()[0]
                                now_time = int(time.time())
                                # 判断cookie是否失效
                                if now_time - cookie[2] < pw_dict["lose_time"]:
                                    data_url = 'http://qun.qq.com/cgi-bin/group_search/pc_group_search'
                                    headers = {
                                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                                        'Host': 'qun.qq.com',
                                        'Origin': 'http://find.qq.com/',
                                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
                                        'Referer': 'http://find.qq.com/',
                                        'Cookie': cookie[0]
                                    }
                                    data = {
                                        'k': '交友',
                                        'n': '8',
                                        'st': '1',
                                        'iso': '1',
                                        'src': '1',
                                        'v': '4903',
                                        'bkn': cookie[1],
                                        'isRecommend': 'false',
                                        'city_id': '{}'.format(j),
                                        'from': '1',
                                        'keyword': '{}'.format(k),
                                        'sort': '2',
                                        'wantnum': '50',
                                        'page': '{}'.format(p),
                                        'ldw': cookie[1]
                                    }
                                    time.sleep(wait_time)
                                    # while True:
                                    #     # 获取ip判断，是否在可用区间
                                    #     heads = {
                                    #         "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
                                    #         "Host": "www.ip138.com"}
                                    #     try:
                                    #         res_ip = requests.get("http://2018.ip138.com/ic.asp", timeout=5)
                                    #         if res_ip.status_code == 200:
                                    #             res_str = res_ip.content.decode("gbk")
                                    #             s1 = res_str.replace("\n", "")
                                    #             ip_data = s1[-24:-59:-1][::-1]
                                    #             if "绍兴" in ip_data:
                                    #                 print("ip地址区间符合要求")
                                    #                 break
                                    #             else:
                                    #                 time.sleep(1)
                                    #                 # change_ip()
                                    #         else:
                                    #             change_ip()
                                    #     except Exception as e:
                                    #         print("获取ip失败 : %s" % e)
                                    #         time.sleep(1)
                                    #         # change_ip()
                                    #         continue
                                    print("BKN: %s" % cookie[1])
                                    try:
                                        res = requests.post(url=data_url, headers=headers, data=data)
                                        str = res.content
                                    except:
                                        logging.info("请求数据失败")
                                        print("请求数据失败")
                                        continue
                                    try:
                                        list = json.loads(str)['group_list']
                                    except:
                                        login_str = str.decode()
                                        if "anti-malicious" in login_str:
                                            logging.info("检测恶意请求，等待...")
                                            print("检测恶意请求，等待...")
                                            cs1.execute(
                                                "SELECT count FROM cookies where cookie='{}';".format(cookie[0]))
                                            cookie_use_count = cs1.fetchone()[0]
                                            cookie_use_count += int(counts)
                                            cs1.execute(
                                                "update cookies set count={} where cookie='{}';".format(
                                                    cookie_use_count,
                                                    cookie[0]))
                                            conn.commit()
                                        else:
                                            conn.ping(reconnect=True)
                                            cs1.execute(
                                                "SELECT count FROM cookies where cookie='{}';".format(cookie[0]))
                                            cookie_use_count = cs1.fetchone()[0]
                                            cookie_use_count += 1
                                            cs1.execute(
                                                "update cookies set count={} where cookie='{}';".format(
                                                    cookie_use_count,
                                                    cookie[0]))
                                            conn.commit()
                                        if j_count < 2:
                                            j_count += 1
                                            logging.info("切换QQ号")
                                            print("切换QQ号")
                                            continue
                                        else:
                                            # 切换城市
                                            break
                                    # 对cookie使用次数进行记录
                                    conn.ping(reconnect=True)
                                    cs1.execute("SELECT count FROM cookies where cookie='{}';".format(cookie[0]))
                                    cookie_use_count = cs1.fetchone()[0]
                                    cookie_use_count += 1
                                    cs1.execute(
                                        "update cookies set count={} where cookie='{}';".format(cookie_use_count,
                                                                                                cookie[0]))
                                    conn.commit()

                                    # 对关键字采集次数进行记录
                                    cs1.execute("select collected_count from vc_keyword where `key`='{}';".format(k))
                                    collect_count = cs1.fetchone()[0]
                                    collect_count += 1
                                    cs1.execute(
                                        "UPDATE vc_keyword SET collected_count={} WHERE `key`='{}';".format(
                                            collect_count, k))
                                    conn.commit()

                                    # 如果采集collect_count次，标记不可采集
                                    # if collect_count >= pw_dict["collect_count"]:
                                    #     cs1.execute("UPDATE vc_keyword SET is_active=0 WHERE `key`='{}';".format(k))
                                    #     conn.commit()
                                    #     update(k)
                                    #     change_k = 1
                                    #     break
                                    logging.info("关键字：%s 页数：%s 个数：%s 城市编号：%s" % (k, p + 1, len(list), j))
                                    print("关键字：%s 页数：%s 个数：%s 城市编号：%s" % (k, p + 1, len(list), j))

                                    # 遍历返回数据列表，逐个处理
                                    for i in list:
                                        up_status = 0
                                        code = int(i["code"])
                                        name = i["name"]
                                        max_member_num = int(i["max_member_num"])
                                        member = int(i["member_num"])
                                        city_list = i["qaddr"]
                                        city_c = ""
                                        if len(city_list) == 0:
                                            city_c = ""
                                        elif len(city_list) == 2:
                                            city_c = city_list[0] + "," + city_list[1]
                                        else:
                                            for c in city_list:
                                                city_c += c
                                        city = city_c
                                        master_qq = int(i["owner_uin"])
                                        option = int(i["option"])
                                        pd = hex(i["flag"] + i["flag_ext"])
                                        t = time.time()
                                        st = int(t)
                                        if pd.endswith("4551"):
                                            public = 1
                                        else:
                                            public = 0
                                        # try:
                                        #     labels_list = i["labels"]
                                        #     if len(labels_list) != 0:
                                        #         for l in labels_list:
                                        #             conn.ping(reconnect=True)
                                        #             count = cs1.execute(
                                        #                 "select * from vc_keyword where `key`='{}';".format(l['label']))
                                        #             if count == 0:
                                        #                 count = cs1.execute(
                                        #                     "select * from vc_keyword_from_label where `key`='{}';".format(
                                        #                         l['label']))
                                        #                 if count == 0:
                                        #                     cs1.execute("insert into vc_keyword_from_label values(0, '{}');".format(
                                        #                         l['label']))
                                        #                     conn.commit()
                                        #                     print("GET标签")
                                        #                 else:
                                        #                     logging.info("关键字已存在")
                                        #                     # print("关键字已存在")
                                        #             else:
                                        #                 logging.info("关键字已存在")
                                        #                 # print("关键字已存在")
                                        # except:
                                        #     logging.info("标签为空")
                                        #     # print("标签为空")
                                        #     try:
                                        #         conn.close()
                                        #     except:
                                        #         pass
                                        try:
                                            conn.ping(reconnect=True)
                                            db = (int(code) // 4000000) + 1
                                            get_count = cs1.execute(
                                                "select qq_group_number from qq_qun{} where qq_group_number={};".format(db,
                                                                                                          code))
                                            if get_count == 1:
                                                cs1.execute(
                                                    "update qq_qun{} set upd_time={} where qq_group_number={};".format(
                                                        db, int(
                                                            time.time()), code))
                                                print("记录已更新")
                                            else:
                                                cs1.execute(
                                                    "insert into qq_qun{} values({},'{}','{}',{},{},{},{},{},'{}',{},NULL,0)".format(
                                                        db, code, name, k, member, max_member_num, master_qq,
                                                        public, option,
                                                        city, st))
                                                print("记录已保存")
                                        except:
                                            logging.info("记录已存在")
                                            # print("记录已存在")
                                        # if member < 50 or option == 3 or option == 5:
                                        #     continue
                                        # try:
                                        #     conn.ping(reconnect=True)
                                        #     count = cs1.execute("select * from vc_qq_group where `qq_group_number`={}".format(code))
                                        #     if count == 0:
                                        #         # 将数据存入总数据库
                                        #         cs1.execute(
                                        #             "insert into vc_qq_group values (0, {}, '{}', {}, {}, {}, {}, {}, NULL, NULL, '{}', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);".format(
                                        #                 code, name, member, max_member_num, master_qq, option, public, city))
                                        #         conn.commit()
                                        #         logging.info("保存数据成功")
                                        #         print("保存数据成功")
                                        #     else:
                                        #         logging.info("数据已存在")
                                        #         # print("数据已存在")
                                        #     try:
                                        #         conn.close()
                                        #     except:
                                        #         pass
                                        # except Exception as e:
                                        #     logging.info("保存数据失败: %s " % e)
                                        #     print("保存数据失败: %s " % e)
                                        #     try:
                                        #         conn.close()
                                        #     except:
                                        #         pass
                                    else:
                                        conn.commit()
                                    # if collect_count >= pw_dict["collect_count"]:
                                    #     cs1.execute("UPDATE vc_keyword SET is_active=0 WHERE `key`='{}';".format(k))
                                    #     conn.commit()
                                    #     update(k)
                                    #     change_k = 1
                                    #     break
                                    break
                                else:
                                    conn.ping(reconnect=True)
                                    cs1.execute("select qq from cookies where time={}".format(cookie[2]))
                                    qq_num = cs1.fetchone()[0]
                                    cs1.execute("update qq_status set status=3 where qq_num='{}';".format(qq_num))
                                    cs1.execute("delete from cookies where time={}".format(cookie[2]))
                                    conn.commit()
                                    continue
                            print("下一页")
                    else:
                        # update(k)
                        # 切换关键字
                        break
                    logging.info("切换地区")
                    print("切换地区")
                cs1.execute("UPDATE vc_keyword SET is_active=0 WHERE `key`='{}';".format(k))
                conn.commit()
                try:
                    conn.close()
                except:
                    pass
                logging.info("切换关键字")
                print("切换关键字")
                #     update(k)
                # update(k)
                # time.sleep(1)
            time.sleep(3)
            try:
                conn.close()
            except:
                pass
        except Exception as e:
            logging.info("循环结束异常，重新循环: %s" % e)
            print("循环结束异常，重新循环")
            time.sleep(150)
            try:
                conn.close()
            except:
                pass


if __name__ == '__main__':
    main()
    print("   ")
