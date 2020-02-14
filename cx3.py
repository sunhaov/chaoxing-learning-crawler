from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox  # 不导入会提示tkinter没有这个属性
from PIL import Image
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os


def login():
    global list_c, s
    # wait_login.place(x=50, y=170)
    try:
        browser.find_element_by_id("unameId").send_keys(entry_usn.get())
        browser.find_element_by_id("passwordId").send_keys(entry_pwd.get())
        browser.find_element_by_id("numcode").send_keys(entry_code.get())
        browser.find_element_by_class_name('zl_btn_right').click()  # 点击登录

        s = get_cookie(browser)  # 登陆之后获取 coolies
        list_c = get_courses_url(s, browser)  # 存放所有小组的链接

        # 显示隐藏的窗口
        window_class.update()
        window_class.deiconify()
    except Exception:
        tk.messagebox.showerror(title='登录失败', message='\n可能是账号密码验证码输入错误，请关闭后重新打开进行登录')
        # 关闭浏览器和驱动
        browser.close()
        browser.quit()
        # 销毁窗口
        window.destroy()


def select_class():
    try:
        global list_a
        select_index = class_list.curselection()  # 选中的所有项的索引
        for si in select_index:
            c_url = list_c[si]
            dis = get_discuss_url(c_url)
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
                grp_a = dis[:28] + t_split[t_split.index(' target=') - 1]
                t_replace = grp_a.replace('&amp;', '&')
                list_a.append(t_replace)

            # 显示隐藏的窗口
            window_count.update()
            window_count.deiconify()
    except Exception as e:
        tk.messagebox.showerror(parent=window_class, title='获取小组失败', message='获取小组失败: ' + str(e))
        window.destroy()  # 销毁窗口


def count_etimes():
    # wait_count.place(x=45, y=420)
    try:
        select_index = tits_list.curselection()  # 选中的所有项的索引
        dic_grp = {}  # 保存各小组发言数
        err_grp = ''  # 保存出错的小组数
        for si in select_index:
            try:
                s_url = list_a[si]
                r = s.get(url=s_url, headers=headers)
                soup = BeautifulSoup(r.text, features='lxml')
                grp_title = tits_list.get(si)
                name_span = soup.find_all('span', {'class': 'name'})
                # 所有人和建贴人名字后边都有空格，盖楼人没有空格
                names = [ns.get_text() for ns in name_span]
                nozz_names = set(names)
                nozz_names.remove(names[1])  # 然后在集合中去掉盖楼人,也就是names的第二个，没有空格的名字
                fayan_num = [n + ': ' + str(names[1:].count(n)) for n in nozz_names]  # 第一个是建贴人，不要建贴人
                dic_grp[grp_title] = fayan_num
            except Exception:
                err_grp = err_grp + str(tits_list.get(si)) + '  '

        if err_grp != '':
            tk.messagebox.showwarning(parent=window_count, title='获取一些小组时出现问题',
                                      message='以下小组的帖子获取数据失败，重试可能会解决问题：\n' + err_grp)

        # 输出统计数据
        export_count(dic_grp)

        # 清空小组并隐藏窗口
        tits_list.delete(0, 'end')
        window_count.withdraw()
        reselect_class.place(x=45, y=230)  # 显示继续选择新的课程
    except Exception as e:
        tk.messagebox.showerror(parent=window_count, title='获取小组失败', message='获取小组失败: ' + str(e))
        window.destroy()  # 销毁窗口


def onselect(evt):
    # Note here that Tkinter passes an event object to onselect()
    w = evt.widget
    ln.config(text='请选择要进行操作的小组\n当前共选择小组个数： ' + str(len(w.curselection())))


def get_numcode(browser):
    browser.get('http://passport2.chaoxing.com/login?fid=&refer=http://i.mooc.chaoxing.com')
    # 获取截图
    browser.get_screenshot_as_file(r'screenshot.png')
    # 截取验证码部分
    img = Image.open("screenshot.png")
    cropped = img.crop((320, 330, 430, 380))  # (left, upper, right, lower)
    cropped.save("screenshot.png")


def get_cookie(browser):
    # 获取 cookies 添加到 requests 里
    cookie = browser.get_cookies()
    c = requests.cookies.RequestsCookieJar()
    for i in cookie:  # 添加cookie到CookieJar
        c.set(i["name"], i["value"])
    # 新建 session
    session = requests.session()
    session.cookies.update(c)  # 更新session里的cookie
    # pickle.dump(session, 'session.cok')
    return session


def get_courses_url(s, browser):
    list_c = []  # 初始化空列表保存课程的url
    # 使用 beautifulsoup 解析登陆后的主页面, 获取毛概课的网页
    html = browser.page_source  # 登陆后的主页面
    soup = BeautifulSoup(html, features='lxml')

    # 居然 html 里嵌套 html，因此要 get 里边的 html
    iframe_s = soup.find_all('iframe')
    for i in iframe_s:
        iframe = i['src']
    browser.get(iframe)
    html_in = browser.page_source
    soup = BeautifulSoup(html_in, features='lxml')
    courses = soup.find_all('h3', {"class": "clearfix"})
    for c in courses:
        class_list.insert('end', c.find('a')['title'])
        list_c.append(c.find('a')['href'])
    return list_c


def get_discuss_url(course):
    # 到这里已经进入毛概课的页面了，下一步解析进入讨论组
    r = s.get(url=course, headers=headers)
    soup = BeautifulSoup(r.text, features='lxml')
    navshow = soup.find('div', {"class": "navshow"})
    ul = navshow.find('ul')
    for li in ul:
        if('讨论' in str(li)):
            discuss_li = li
            break
    discuss = str(discuss_li).split('"')[1]
    disc = discuss.replace('&amp;', '&')
    dis = course[:28] + disc  # 讨论组的网页
    return dis


def export_count(dic_grp):
    try:
        files = [('Excel工作簿', '*.xlsx'), ('记事本', '*.txt')]
        filepath = tkinter.filedialog.asksaveasfile(parent=window_count, filetypes=files, defaultextension=files,
                                                    initialfile='慕课成员发言数.xlsx', title='请选择文件保存位置')
        file_root, tempfilename = os.path.split(filepath.name)
        filename, extension = os.path.splitext(tempfilename)

        if extension == '.txt':
            with open(filepath.name, 'w', encoding='utf-8') as f:
                for key in dic_grp:
                    f.write(str(key))
                    f.write(str(dic_grp[key]))
                    f.write('\n')
                    f.write('\n')
            tk.messagebox.showinfo(parent=window_count, title='完成', message='文件已保存在: ' + filepath.name)

        elif extension == '.xlsx':
            # 输出到 EXCEL
            df = pd.DataFrame.from_dict(dic_grp, orient='index')  # 避免value长度不一致报错
            df.transpose()
            writer = pd.ExcelWriter(filepath.name)
            pd.DataFrame(df).to_excel(writer, 'Sheet1')
            writer.save()
            writer.close()
            tk.messagebox.showinfo(parent=window_count, title='完成', message='文件已保存在: ' + filepath.name)  # 提示信息对话窗

    except Exception as e:
        tk.messagebox.showerror(parent=window_count, title='导出文件失败', message='导出文件失败: ' + str(e))
        window.destroy()  # 销毁窗口


# 定义窗口
window = tk.Tk()
window.title('慕课小助手')
window.geometry('300x210')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}

try:
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 设置chrome浏览器无界面模式
    chrome_options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    browser = webdriver.Chrome(options=chrome_options)

    # s = pickle.load('session.cok')

    get_numcode(browser)  # 获取验证码
except Exception as e:
    tk.messagebox.showerror(title='连接失败',
                            message=str(e) + '连接失败，请检查：\n1.是否安装Google Chrome浏览器\n2.设置Chrome driver所在目录为变量\n3.网络环境是否良好')
    # 关闭浏览器
    browser.close()  # 不是不打开，只是隐藏了，所以还是要关闭
    # 关闭chreomedriver进程
    browser.quit()
    # 销毁窗口
    window.destroy()


entry_usn = tk.Entry(window, show=None)
entry_usn.place(x=10, y=20)
entry_pwd = tk.Entry(window, show='*')
entry_pwd.place(x=10, y=70)
entry_code = tk.Entry(window, show=None)
entry_code.place(x=10, y=120)

tk.Label(window, text='手机号/账号').place(x=160, y=20)
tk.Label(window, text='密码').place(x=160, y=70)
# wait_login = tk.Label(window, text='正在登录，请稍等')

canvas = tk.Canvas(window, height=50, width=100)
image_file = tk.PhotoImage(file='screenshot.png')  # 创造一个变量存放ins.gif这张图片
image = canvas.create_image(0, 0, anchor='nw', image=image_file)
canvas.place(x=160, y=100)

b = tk.Button(window, width=13, text='登录', command=login)
b.place(x=160, y=160)


# 定义一个新窗口，用来选择要进行操作的课程
window_class = tk.Toplevel(window)
window_class.geometry('400x270')
window_class.title('课程统计')
num_g = 0  # 选中的组数
tk.Label(window_class, text='请选择要进行操作的课程', font=('Arial', 12), justify='left').place(x=10, y=5)
reselect_class = tk.Label(window_class, text='继续选择需要统计的课程')
# 创建滚动条
sb1 = tk.Scrollbar(window_class)
sb1.pack(side='right', fill='y')
# 创建 listbox
class_list = tk.Listbox(window_class, width=33, height=8, font=('Arial', 14), yscrollcommand=sb1.set)
class_list.place(x=10, y=30)
# 执行按钮
tk.Button(window_class, width=13, text='执行', command=select_class).place(x=185, y=230)
window_class.withdraw()  # 隐藏窗口


# 定义一个新窗口，用来选择要进行操作的小组
window_count = tk.Toplevel(window)
window_count.geometry('310x450')
window_count.title('各组成员发言次数')
num_g = 0  # 选中的组数
ln = tk.Label(window_count, text='请选择要进行操作的小组\n当前共选中' + str(num_g) + '个小组',
              font=('Arial', 12), justify='left')
ln.place(x=10, y=0)
# wait_count = tk.Label(window_count, text='正在执行操作，请稍等...')
# 创建滚动条
sb = tk.Scrollbar(window_count)
sb.pack(side='right', fill='y')
# 创建 listbox，参数分别是多选（按住ctrl或shift），宽度，高度（容纳的条数），垂直滚动条
tits_list = tk.Listbox(window_count, selectmode='extended', width=40, height=20, yscrollcommand=sb.set)
tits_list.place(x=5, y=40)
tits_list.bind('<<ListboxSelect>>', onselect)
# 执行按钮
exe = tk.Button(window_count, width=13, text='执行', command=count_etimes)
exe.place(x=185, y=410)
window_count.withdraw()  # 隐藏窗口

window.mainloop()
