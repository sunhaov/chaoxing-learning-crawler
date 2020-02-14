from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox  # 不导入会提示tkinter没有这个属性
from PIL import Image
import requests
from bs4 import BeautifulSoup
import time
import threading
import pandas as pd

# 定义窗口
window = tk.Tk()
window.title('慕课小助手')
window.geometry('300x210')

act = 0  # 定义一个变量来判断是否往后执行
err = 0  # 判断错误原因

try:
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 设置chrome浏览器无界面模式
    chrome_options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    browser = webdriver.Chrome(options=chrome_options)
    browser.get('http://passport2.chaoxing.com/login?fid=&refer=http://i.mooc.chaoxing.com')
    # 获取截图
    browser.get_screenshot_as_file(r'screenshot.png')
    # 截取验证码部分
    img = Image.open("screenshot.png")
    cropped = img.crop((320, 330, 430, 380))  # (left, upper, right, lower)
    cropped.save("screenshot.png")
except Exception:
    tk.messagebox.showerror(title='连接失败', message='连接失败，请检查：\n1.是否安装Google Chrome浏览器\n2.设置Chrome driver所在目录为变量')
    # 关闭浏览器
    browser.close()  # 不是不打开，只是隐藏了，所以还是要关闭
    # 关闭chreomedriver进程
    browser.quit()


def login():
    global act, num_g, err
    try:
        browser.find_element_by_id("unameId").send_keys(entry_usn.get())
        browser.find_element_by_id("passwordId").send_keys(entry_pwd.get())
        browser.find_element_by_id("numcode").send_keys(entry_code.get())
        browser.find_element_by_class_name('zl_btn_right').click()  # 点击登录

        # 获取 cookies 添加到 requests 里
        cookie = browser.get_cookies()
        c = requests.cookies.RequestsCookieJar()
        for i in cookie:  # 添加cookie到CookieJar
            c.set(i["name"], i["value"])
        # 新建 session
        s = requests.session()
        s.cookies.update(c)  # 更新session里的cookie

        # 使用 beautifulsoup 解析登陆后的主页面, 获取毛概课的网页
        html = browser.page_source  # 登陆后的主页面
        soup = BeautifulSoup(html, features='lxml')

        # 居然 html 里嵌套 html，因此要 get 里边的 html
        iframe_s = soup.find_all('iframe')
        for i in iframe_s:
            iframe = i['src']  # 获取验证码图片来源
        browser.get(iframe)
        html_in = browser.page_source
        soup = BeautifulSoup(html_in, features='lxml')
        maogai = soup.find('div', {"class": "Mcon1img httpsClass"})  # 找的是排在第一个位置的课
        mg = str(maogai).split('"')[3]  # 转换为字符串并进行切分,取出想要的链接
        # 对比真正网站的 url 发现相比提取出来的 url，没有 amp;
        maog = mg.replace('&amp;', '&')  # 毛概课网页

        # 到这里已经进入毛概课的页面了，下一步解析进入讨论组
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}
        r = s.get(url=maog, headers=headers)
        soup = BeautifulSoup(r.text, features='lxml')
        navshow = soup.find('div', {"class": "navshow"})
        ul = navshow.find('ul')
        for li in ul:
            if('讨论' in str(li)):
                discuss_li = li
                break
        discuss = str(discuss_li).split('"')[1]
        disc = discuss.replace('&amp;', '&')
        dis = maog[:28] + disc  # 讨论组的网页

        # 进入讨论组之后，再解析一次网页
        r = s.get(url=dis, headers=headers)
        soup = BeautifulSoup(r.text, features='lxml')
        title = soup.find_all('h3', {'class': 'bt ol'})  # 所有标题

        list_a = []  # 存放所有小组的链接
        # 把各组标题列出
        for t in title:
            tits_list.insert('end', t.get_text())
            # 提取出链接
            t_split = str(t).split('"')
            grp_a = maog[:28] + t_split[t_split.index(' target=') - 1]
            t_replace = grp_a.replace('&amp;', '&')
            list_a.append(t_replace)

        # 显示隐藏的窗口
        window_count.update()
        window_count.deiconify()

        while(act == 0):
            time.sleep(0.7)
            select_index = tits_list.curselection()  # 选中的所有项的索引
            num_g = len(select_index)
            ln.config(text='请选择要进行操作的小组\n当前共选择小组个数： ' + str(num_g))
            # print('暂停')
        # print('回复')
        dic_grp = {}  # 保存各小组发言数
        for si in select_index:
            s_url = list_a[si]
            r = s.get(url=s_url, headers=headers)
            soup = BeautifulSoup(r.text, features='lxml')
            reply_title = soup.find_all('h3', {'class': 'bt ol'})  # 所有标题
            for i, t in enumerate(reply_title):
                if(i == 0):
                    grp_title = t.get_text().strip()
                    dic_grp[grp_title] = 0  # 0是随便写的,给发言数留的地方
                else:
                    break
            name_span = soup.find_all('span', {'class': 'name'})
            # 所有人和建贴人名字后边都有空格，盖楼人没有空格
            names = [ns.get_text() for ns in name_span]
            nozz_names = set(names)
            nozz_names.remove(names[1])  # 然后在集合中去掉盖楼人,也就是names的第二个，没有空格的名字
            fayan_num = [n + ': ' + str(names[1:].count(n)) for n in nozz_names]  # 第一个是建贴人，不要建贴人
            dic_grp[grp_title] = fayan_num

        for key in dic_grp:
            print(key)
            print(dic_grp[key])
            print('\n')

        # 输出到 EXCEL
        df = pd.DataFrame.from_dict(dic_grp, orient='index')  # 避免value长度不一致报错
        df.transpose()
        files = [('Excel工作簿', '*.xlsx')]
        filepath = tkinter.filedialog.asksaveasfile(parent=window_count, filetypes=files, defaultextension=files,
                                                    initialfile='慕课成员发言数.xlsx', title='请选择文件保存位置')
        writer = pd.ExcelWriter(filepath.name)
        pd.DataFrame(df).to_excel(writer, 'Sheet1')
        writer.save()
        writer.close()
        tk.messagebox.showinfo(parent=window_count, title='完成', message='文件已保存在: ' + filepath.name)  # 提示信息对话窗
    except Exception:
        err = 3
    finally:
        if err != 0:
            tk.messagebox.showerror(title='运行时出现错误',
                                    message='\n1.请检查网络环境\n2.可能是账号密码验证码输入错误，请关闭后重新打开进行登录\n3.其他很多原因...请重试，或者联系开发人员')
        # 关闭浏览器
        browser.close()  # 不是不打开，只是隐藏了，所以还是要关闭
        # 关闭chreomedriver进程
        browser.quit()
        # 销毁窗口
        window.destroy()


def execute():
    global act
    act = 1
    tk.Label(window_count, text='正在执行操作，请稍等...').place(x=45, y=420)  # 提示信息对话窗


def begin():
    '''
    创建多线程，便于控制 login 函数的开始和暂停
    '''
    global act
    t = threading.Thread(target=login)
    t.start()
    tk.Label(window, text='正在登录，请稍等').place(x=50, y=170)


entry_usn = tk.Entry(window, show=None)
entry_usn.place(x=10, y=20)
entry_pwd = tk.Entry(window, show='*')
entry_pwd.place(x=10, y=70)
entry_code = tk.Entry(window, show=None)
entry_code.place(x=10, y=120)

tk.Label(window, text='手机号/账号').place(x=160, y=20)
tk.Label(window, text='密码').place(x=160, y=70)

canvas = tk.Canvas(window, height=50, width=100)
image_file = tk.PhotoImage(file='screenshot.png')  # 创造一个变量存放ins.gif这张图片
image = canvas.create_image(0, 0, anchor='nw', image=image_file)
canvas.place(x=160, y=100)

# 定义一个新窗口，用来选择要进行操作的小组
window_count = tk.Toplevel(window)
window_count.geometry('310x450')
window_count.title('各组成员发言次数')
num_g = 0  # 选中的组数
ln = tk.Label(window_count, text='请选择要进行操作的小组\n当前共选中' + str(num_g) + '个小组',
              font=('Arial', 12), justify='left')
ln.place(x=10, y=0)
# 创建滚动条
sb = tk.Scrollbar(window_count)
sb.pack(side='right', fill='y')
# 创建 listbox，参数分别是多选（按住ctrl或shift），宽度，高度（容纳的条数），垂直滚动条
tits_list = tk.Listbox(window_count, selectmode='extended', width=40, height=20, yscrollcommand=sb.set)
tits_list.place(x=5, y=40)
# 执行按钮
exe = tk.Button(window_count, width=13, text='执行', command=execute)
exe.place(x=185, y=410)
window_count.withdraw()  # 隐藏窗口，在用户输入的时候建窗口，可以减少以后的等待时间

b = tk.Button(window, width=13, text='登录', command=begin)
b.place(x=160, y=160)

window.mainloop()
