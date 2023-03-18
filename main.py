from PyQt5.QtWidgets import QApplication
from mainwindow import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
import sys,csv
from collections import defaultdict
import multiprocessing
from multiprocessing import Process, Manager
import time
import RS485
path = './DEV_RS485.csv'
ls=[]
ct=0

# class MyProcess(QtCore.QProcess):
#     def __init__(self):
#         super().__init__()
#         self.readyRead.connect(self.on_ready_read)
#
#     def on_ready_read(self):
#         message = self.readAll().data().decode()
#         print(f'Received message: {message}')

class DemoMain(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, shared_data):
        # 初始化父类
        super().__init__()
        # self.ls_flag = ls_flag
        # self.ls_data = ls_data
        # self.ls_time = ls_time

        self.shared_data=shared_data
        #多进程传参
        #self.shared_data = shared_data
        # 调用Ui_Form的setupUi()方法构建页面
        self.setupUi(self)
        self.ls = []  # 存放所有子节点
        self.loadData()
        self.retranslateUi(self)
        self.setree()
        self.pushButton.clicked.connect(self.save)

        #定时器，定时更新数据
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateData)
        self.timer.start(100)#1000=1s

    def loadData(self):
        # 迭代读取，有序字典
        with open(path) as stream:
            reader = csv.reader(stream)
            # ignore the header
            next(reader)
            # convert to nested dicts/lists
            self.data = defaultdict(lambda: defaultdict(list))
            for record in reader:
                self.data[record[0]][record[5]].append(record[1:4])
        #print(self.data)

    def setree(self):
        self.treeWidget.setColumnCount(5)  # 设置树结构中的列数
        self.treeWidget.setHeaderLabels(["目录", "采集器ID", "采集器ADD", '设备数据', '采样时间'])  # 设置列标题名
        self.treeWidget.setColumnWidth(0, 300)
        self.treeWidget.setColumnWidth(1, 150)
        self.treeWidget.setColumnWidth(2, 150)
        root = QtWidgets.QTreeWidgetItem(self.treeWidget)  # 创建节点
        root.setText(0, "转换炉")  # 设置根节点文本
        root.setCheckState(0, 0)  # 设置第二列的值
        for row, (text1, values) in enumerate(self.data.items()):  # 遍历字典
            child = QtWidgets.QTreeWidgetItem(root)  # 创建子节点
            child.setText(0, text1)  # 设置第一列的文本
            child.setCheckState(0, 0)
            # child.setText(1, value)  # 设置第二列的文本
            # self.treeWidget.addTopLevelItem(root)  # 将创建的树节点添加到树控件中
            for row, (text2, values) in enumerate(values.items()):  # 遍历字典
                subchild = QtWidgets.QTreeWidgetItem(child)  # 创建子节点
                subchild.setText(0, text2)  # 设置第一列的值
                subchild.setCheckState(0, 0)
                for text3 in values:  # 遍历字典
                    subsubchild = QtWidgets.QTreeWidgetItem(subchild)  # 创建子节点
                    self.ls.append(subsubchild)
                    subsubchild.setText(0, text3[0])  # 设置第一列的值
                    subsubchild.setText(1, text3[1])  # 设置第二列的值
                    subsubchild.setText(2, text3[2])  # 设置第三列的值
                    subsubchild.setText(3, '--')
                    subsubchild.setText(4, '--:--')
                    subsubchild.setCheckState(0, 0)  # 复选框
                # child.setText(2, values[1][])  # 设置第三列的值
                # self.treeWidget.setAlternatingRowColors(True)#行之间交替颜色
        self.ls_flag = list(map(lambda x: 0, range(len(self.ls))))
        self.treeWidget.addTopLevelItem(root)  # 将创建的树节点添加到树控件中
        self.treeWidget.itemChanged.connect(self.subcheckboxStateChanged)

    # 子节点跟随和父节点状态选择
    def subcheckboxStateChanged(self, item, column):  # 选中树形列表中的父节点，子节点全部选中
        count = item.childCount()  # 子节点个数
        if item.checkState(column) == 0:
            for f in range(count):
                item.child(f).setCheckState(0, 0)
            self.parentcheckboxStateChanged0(item)

        if item.checkState(column) == 1:
            self.parentcheckboxStateChanged1(item)

        if item.checkState(column) == 2:
            for f in range(count):
                item.child(f).setCheckState(0, 2)
            self.parentcheckboxStateChanged2(item)

    # 父节点取消选中
    def parentcheckboxStateChanged0(self, item):  # 状态2为选中，状态0为未选
        flag = 0
        parent = QtWidgets.QTreeWidgetItem.parent(item)
        if parent is not None:
            count = parent.childCount()
            for f in range(count):
                if parent.child(f).checkState(0) != 0:
                    flag = 1
            if flag == 0:
                parent.setCheckState(0, 0)
            else:
                parent.setCheckState(0, 1)

    ##父节点半选
    def parentcheckboxStateChanged1(self, item):
        parent = QtWidgets.QTreeWidgetItem.parent(item)
        if parent is not None:
            parent.setCheckState(0, 1)

    # 父节点选中
    def parentcheckboxStateChanged2(self, item):
        flag = 1
        parent = QtWidgets.QTreeWidgetItem.parent(item)
        if parent is not None:
            if parent.checkState(0) == 0 or 1:
                count = parent.childCount()
                for f in range(count):
                    if parent.child(f).checkState(0) == 0:
                        flag = 0
                if flag == 1:
                    parent.setCheckState(0, 2)
                else:
                    parent.setCheckState(0, 1)

    def save(self):
        for i in range(len(self.ls)):
            if self.ls[i].checkState(0) == 2:
                temp = self.shared_data['flag']
                temp[i] = 1
                self.shared_data['flag'] = temp
            else:
                temp = self.shared_data['flag']
                temp[i] = 0
                self.shared_data['flag'] = temp
        print(self.shared_data['flag'])
        # self.shared_data['message'] = self.ls_flag

    def updateData(self):
        # 在这里更新数据，并更新 UI 界面上的标签显示内容
        # 这里假设要显示的数据是一个字符串类型的变量 data
        for i in range(len(self.ls)):
            if self.shared_data['flag'][i] == 1:
                self.ls[i].setText(3, str(self.shared_data['data'][i]))
                self.ls[i].setText(4, str(self.shared_data['time'][i]))

def show(shared_data):
    app = QApplication(sys.argv)
    # 实例化页面并展示
    demo = DemoMain(shared_data)
    demo.show()
    sys.exit(app.exec_())

def checkflag(shared_data):
    while True:
        #for i in range(len(shared_data['flag'])):
            #if shared_data['flag'][i] == 1:
        #print("Current count:", ls_flag)

        for i in range(len(shared_data['flag'])):
            temp_data = shared_data['data']
            temp_time = shared_data['time']
            if shared_data['flag'][i] == 1:
                data,now_time=RS485.communcation(i)
                temp_data[i] = data
                temp_time[i] = now_time
            shared_data['data'] = temp_data
            shared_data['time'] = temp_time
        #print("Current count:",shared_data['flag'])
        time.sleep(1)



if __name__ == '__main__':
    with open(path) as stream:
        reader = csv.reader(stream)
        # ignore the header
        next(reader)
        # convert to nested dicts/lists
        data = defaultdict(lambda: defaultdict(list))
        for record in reader:
           ct=ct+1
    ls_flag = list(map(lambda x: 0, range(ct)))
    ls_data = list(map(lambda x: '--', range(ct)))
    ls_time = list(map(lambda x: '--:--', range(ct)))
    manager = Manager()
    shared_data = manager.dict({'flag': ls_flag, 'data': ls_data, 'time':ls_time})
    # ls_data = manager.list(ls_data)
    # ls_time = manager.list(ls_time)
    # p1 = Process(target=show, args=(ls_flag, ls_data, ls_time,))
    # p2 = Process(target=checkflag, args=(ls_flag, ls_data, ls_time,))
    p1 = Process(target=show, args=(shared_data,))
    p2 = Process(target=checkflag, args=(shared_data,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
