import serial
import crcmod
import datetime
import time
import struct
import sql
# CRC16校验，返回整型数
def crc16(veritydata):
    if not veritydata:
        return
    crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    return crc16(veritydata)

# 校验数据帧的CRC码是否正确
def checkcrc(data):
    if not data:
        return False
    if len(data) <= 2:
        return False
    nocrcdata = data[:-2]
    oldcrc16 = data[-2:]
    oldcrclist = list(oldcrc16)
    crcres = crc16(nocrcdata)
    crc16byts = crcres.to_bytes(2, byteorder="little", signed=False)
    # print("CRC16:", crc16byts.hex())
    crclist = list(crc16byts)
    if oldcrclist[0] != crclist[0] or oldcrclist[1] != crclist[1]:
        return False
    return True

# Modbus-RTU协议的03或04读取保存或输入寄存器功能主-》从命令帧
def mmodbus03or04(add, startregadd, regnum, funcode=3):
    # add：Modbus从站地址（仪表地址）
    # startregadd：要读取的开始寄存器地址（从0开始的绝对地址）
    # regnum：要读取的寄存器个数
    # funcode：功能号，默认值是3
    if add < 0 or add > 0xFF or startregadd < 0 or startregadd > 0xFFFF or regnum < 1 or regnum > 0x7D:
        print("Error: parameter error")
        return
    if funcode != 3 and funcode != 4:
        print("Error: parameter error")
        return
    sendbytes = add.to_bytes(1, byteorder="big", signed=False)#转进制，大端符合传输，小段符合计算机存储
    sendbytes = sendbytes + funcode.to_bytes(1, byteorder="big", signed=False) + startregadd.to_bytes(2, byteorder="big", signed=False) + \
                regnum.to_bytes(2, byteorder="big", signed=False)
    crcres = crc16(sendbytes)
    crc16bytes = crcres.to_bytes(2, byteorder="little", signed=False)
    sendbytes = sendbytes + crc16bytes
    return sendbytes

# Modbus-RTU协议的03或04读取保持或输入寄存器功能从-》主的数据帧解析（浮点数2,1,4,3格式，16位短整形（定义正负数））
def smodbus03or04(recvdata, valueformat=0, intsigned=False):
    # recvdata：Modbus - RTU从站在接收03和04功能号命令帧后的发回主站的数据帧，bytes字节串类型。
    # valueformat：寄存器中值的格式，0
    # 代表用2个寄存器4个字节表示一个单精度浮点数，1
    # 代表1个寄存器（2字节）存放1个16位整形值，默认为0,（仪表用的是单精度浮点数）
    # intsigned：当寄存器数据值格式是整形时，true则按照有符号整形转换，false则按无符号整形转换。

    if not recvdata:
        print("Error: data error")
        return
    if not checkcrc(recvdata):
        print("Error: crc error")
        return
    datalist = list(recvdata)
    print(datalist)
    if datalist[1] != 0x3 and datalist[1] != 0x4:
        print("Error: recv data funcode error")
        return
    bytenums = datalist[2]
    if bytenums % 2 != 0:
        print("Error: recv data reg data error")
        return
    retdata = []

    # 01 03 14 /00 00 00 42/ 00 00 00 00/ 00 00 00 00/ 07 31/ 00 00 69 78/ 08 42/ 48 82
    # 通信地址01
    # 回复功能码03
    # 回复的字节数0x14代表20
    # 通道状态
    # 浓度（整型）
    # 浓度（浮点型）
    # AD值1841
    # 温度值27℃
    # 温度AD值2114
    # 校验

    if valueformat == 0:
        num=recvdata[7:11]
        num=int.from_bytes(num, byteorder="big", signed=False)
        num=num/1000
        print(num)
        # floatnums = bytenums / 4
        # print("float nums: ", str(floatnums))
        # floatlist = [0, 0, 0, 0]
        # for i in range(int(floatnums)):
        #     floatlist[1] = datalist[3+i*4]
        #     floatlist[0] = datalist[4+i*4]
        #     floatlist[3] = datalist[5+i*4]
        #     floatlist[2] = datalist[6+i*4]
        #     bfloatdata = bytes(floatlist)
        #     [fvalue] = struct.unpack('f', bfloatdata)
        #     retdata.append(fvalue)
        #     print(f'Data{i+1}: {fvalue:.3f}')
    elif valueformat == 1:
        shortintnums = bytenums / 2
        print("short int nums: ", str(shortintnums))
        for i in range(int(shortintnums)):
            btemp = recvdata[3+i*2:5+i*2]
            shortvalue = int.from_bytes(btemp, byteorder="big", signed=intsigned)
            retdata.append(shortvalue)
            print(f"Data{i+1}: {shortvalue}")
    return num

def communcation(add):
    slaveadd = add
    startreg = 40000
    regnums = 10
    send_data = mmodbus03or04(slaveadd, startreg, regnums)
    #print("send data : ", send_data.hex())
    try:
        com = serial.Serial("com9", 9600, timeout=0.1)
    except:
        return '未连接', '未连接'
    else:
        #starttime = time.time()
        com.write(send_data)
        recv_data = com.read(regnums*2+5)
        #endtime = time.time()
        other_StyleTime = datetime.datetime.now()
        # if len(recv_data) > 0:
        #     print("recv: ", recv_data.hex())
        # print(f"used time: {endtime-starttime:.3f}")
        com.close()
        data=smodbus03or04(recv_data)
        if data==None:
            return '连接失败', other_StyleTime
        else:
            sql.insert_data_to_db(add, data, str(other_StyleTime))
            return data, other_StyleTime
