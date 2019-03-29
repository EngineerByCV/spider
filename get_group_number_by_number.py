import os
import sys
import time
import json
import socket
import random
import logging
import requests
from pymysql import *

# 添加debug日志
LOG_FORMAT = '%(asctime)s %(filename)s %(message)s'
logging.basicConfig(filename='get_group_number_by_number_logging.txt', level=logging.DEBUG, format=LOG_FORMAT)


def change_start_num(num):
    with open('./pw', 'r') as f:
        statue_dict = json.loads(f.read())
        statue_dict["start_num"] = num

    with open('./pw', "w") as f:
        json.dump(statue_dict, f, ensure_ascii=False)
        f.close()


def main():
    while True:
        logging.info("开始新一轮循环")
        try:
            # 获取数据
            with open("./pw", 'r') as f:
                pw_str = f.read()
            pw_dict = json.loads(pw_str)
            start_num = pw_dict["start_num"]
            end_num = pw_dict["end_num"]
            conn = connect(host='localhost', port=3306, database='vc_qq', user='root',
                           password=pw_dict["password"],
                           charset='utf8')
            # 获得Cursor对象
            cs1 = conn.cursor()
            # 遍历关键字列表
            for k in range(start_num, end_num):
                logging.info("号码：%s " % k)
                print("号码：%s " % k)
                cc_count = 1
                while cc_count < 2:
                    conn.ping(reconnect=True)
                    counts = cs1.execute("SELECT count FROM cookies order by count;")
                    cookie_count = cs1.fetchall()[0][0]
                    if counts < 3:
                        print("cookie数量过少")
                        time.sleep(20)
                        conn.close()
                        cc_count = 1
                    else:
                        cc_count = 2
                # 选用使用次数少的qq号采集
                try_count = 0
                while try_count < 2:
                    conn.ping(reconnect=True)
                    counts = cs1.execute("SELECT count FROM cookies order by count;")
                    cookie_count = cs1.fetchall()[0][0]
                    cs1.execute("SELECT cookie,bkn,time FROM cookies where count={};".format(cookie_count))
                    cookie = cs1.fetchall()[0]
                    now_time = int(time.time())
                    # 判断cookie是否失效
                    if now_time - cookie[2] < pw_dict["lose_time"]:
                        data_url = 'http://qun.qq.com/cgi-bin/group_search/pc_group_search'
                        headers = {
                            'Accept': 'application/json, text/javascript, */*; q=0.01',
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
                            'city_id': '0',
                            'from': '1',
                            'newSearch': 'true',
                            'keyword': '{}'.format(k),
                            'sort': '0',
                            'wantnum': '24',
                            'page': '0',
                            'ldw': cookie[1]
                        }
                        # time.sleep(random.uniform(0.8, 1.2))

                        # 对cookie使用次数进行记录
                        conn.ping(reconnect=True)
                        cs1.execute("SELECT count FROM cookies where cookie='{}';".format(cookie[0]))
                        cookie_use_count = cs1.fetchone()[0]
                        cookie_use_count += 1
                        cs1.execute(
                            "update cookies set count={} where cookie='{}';".format(cookie_use_count, cookie[0]))
                        conn.commit()
                        while True:
                            try:
                                ipList = socket.gethostbyname_ex(socket.gethostname())
                                if len(ipList[-1]) == 2:
                                    print("违法ip")
                                    time.sleep(2)
                                    continue
                                else:
                                    break
                            except:
                                time.sleep(2)
                        try:
                            time.sleep(3 / counts)
                            # logging.info(data)
                            res = requests.post(url=data_url, headers=headers, data=data)
                            str = res.content
                        except:
                            logging.info("请求数据失败")
                            print("请求数据失败")
                            try_count += 1
                            continue
                        try:
                            list = json.loads(str)['group_list']
                        except:
                            login_str = str.decode()
                            if "anti-malicious" in login_str:
                                logging.info("检测恶意请求，等待...")
                                print("检测恶意请求，等待...")
                                time.sleep(2)
                                continue
                            elif "login" in login_str:
                                conn.ping(reconnect=True)
                                cs1.execute("select qq from cookies where time={}".format(cookie[2]))
                                qq_num = cs1.fetchone()[0]
                                cs1.execute("update qq_status set status=3 where qq_num='{}';".format(qq_num))
                                cs1.execute("delete from cookies where time={}".format(cookie[2]))
                                conn.commit()
                                continue
                            else:
                                print("号码不存在")
                                break

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
                                logging.info("记录异常")
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
                        break
                    else:
                        conn.ping(reconnect=True)
                        cs1.execute("select qq from cookies where time={}".format(cookie[2]))
                        qq_num = cs1.fetchone()[0]
                        cs1.execute("update qq_status set status=3 where qq_num='{}';".format(qq_num))
                        cs1.execute("delete from cookies where time={}".format(cookie[2]))
                        conn.commit()
                print("  ")
            print("关键词结束")
            try:
                conn.close()
            except:
                pass
        except Exception as e:
            logging.info("循环结束异常，重新循环: %s" % e)
            print("循环结束异常，重新循环")
            change_start_num(k)
            time.sleep(150)
            try:
                conn.close()
            except:
                pass


if __name__ == '__main__':
    main()
    print("   ")
