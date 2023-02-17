# coding:utf8

import torch
import torch.nn as nn
import numpy as np
import random
import json
import matplotlib.pyplot as plt

"""

基于pytorch框架编写模型训练
实现一个自行构造的找规律(机器学习)任务
规律：x是一个6维向量，如果第1个数>第2个数+第5个数，则为正样本，反之为负样本

"""


class TorchModel(nn.Module):
    def __init__(self, input_size):
        super(TorchModel, self).__init__()
        self.linear = nn.Linear(input_size, 1)  # 线性层
        #----------------------------------------------------------------------------
        #这里只用了1个线性层的神经网络。神经网络的传递：[1*5]的矩阵*[5*3]矩阵*[3*4]矩阵=[1*4]矩阵
        #通常，[5*3]*[4*3]是不能做卷积的，可以用转置矩阵：[5*3]*[3*4]
        #矩阵的点乘：[1,2,3]。[4,5,6]=1*4+2*5+3*6
        #----------------------------------------------------------------------------
        self.activation = torch.sigmoid  # sigmoid归一化函数  激活函数，使得可以非线性化，可以更好的拟合
        self.loss = nn.functional.mse_loss  # loss函数 此处采用均方差损失

    # 当输入真实标签，返回loss值；无真实标签，返回预测值
    def forward(self, x, y=None):
        x = self.linear(x)  # (batch_size, input_size) -> (batch_size, 1)
        y_pred = self.activation(x)  # (batch_size, 1) -> (batch_size, 1)
        if y is not None:
            return self.loss(y_pred, y)  # 预测值和真实值计算损失
        else:
            return y_pred  # 输出预测结果


# 生成一个样本, 样本的生成方法，代表了我们要学习的规律
# 随机生成一个6维向量，如果第一个值大于第二个与第五个的和，认为是正样本，反之为负样本
def build_sample():
    x = np.random.random(6)
    if x[0] > x[1]+x[4]:
        return x, 1
    else:
        return x, 0


# 随机生成一批样本
# 正负样本均匀生成
def build_dataset(total_sample_num):
    X = []
    Y = []
    for i in range(total_sample_num):
        x, y = build_sample()
        X.append(x)    #[[6维向量],[6维向量],[6维向量],[6维向量]...]  合起来是一个张量
        Y.append([y])  #这里要上[]，是因为[2,3,4,5...]在torch中，默认的会是标量，加上后会是[[2],[3],[4],[5]...]才是张量
    return torch.FloatTensor(X), torch.FloatTensor(Y)


# 测试代码
# 用来测试每轮模型的准确率
def evaluate(model):
    model.eval()
    test_sample_num = 200  #用200个样本来验证他的准确率
    x, y = build_dataset(test_sample_num)
    print("本次预测集中共有%d个正样本，%d个负样本" % (sum(y), test_sample_num - sum(y)))
    correct, wrong = 0, 0
    with torch.no_grad(): #关闭梯度，表示不是在学习，而是在验证
        y_pred = model(x)  # 模型预测
        for y_p, y_t in zip(y_pred, y):  # 与真实标签进行对比 zip把两个组合在一起
            if float(y_p) < 0.5 and int(y_t) == 0:
                correct += 1  # 负样本判断正确
            elif float(y_p) >= 0.5 and int(y_t) == 1:
                correct += 1  # 正样本判断正确
            else:
                wrong += 1
    print("正确预测个数：%d, 正确率：%f" % (correct, correct / (correct + wrong)))
    return correct / (correct + wrong)


def main():
    # 配置参数
    epoch_num = 50  # 训练轮数
    #规则变得复杂一点，就增加训练的轮数，进而提高训练的准确度
    batch_size = 20  # 每次训练样本个数
    train_sample = 6000  # 每轮训练总共训练的样本总数
    input_size = 6  # 输入向量维度
    learning_rate = 0.001  # 学习率
    # 建立模型
    model = TorchModel(input_size)
    # 选择优化器
    optim = torch.optim.Adam(model.parameters(), lr=learning_rate)
    log = [] #存放画图用的数据
    # 创建训练集，正常任务是读取训练集
    train_x, train_y = build_dataset(train_sample)
    # 训练过程
    for epoch in range(epoch_num):
        model.train()
        watch_loss = [] #存放每一轮里面每一段的loss值，然后再平均，避免loss出现突兀的点
        for batch_index in range(train_sample // batch_size):  #train_sample // batch_size 对该轮的样本分段
            x = train_x[batch_index * batch_size : (batch_index + 1) * batch_size] #切片
            y = train_y[batch_index * batch_size : (batch_index + 1) * batch_size] #切片
            optim.zero_grad()  # 梯度归零
            loss = model(x, y)  # 计算loss
            loss.backward()  # 计算梯度
            optim.step()  # 更新权重
            watch_loss.append(loss.item())
        print("=========\n第%d轮平均loss:%f" % (epoch + 1, np.mean(watch_loss))) #mean()是取平均值
        acc = evaluate(model)  # 测试本轮模型结果
        log.append([acc, float(np.mean(watch_loss))])
    # 保存模型
    torch.save(model.state_dict(), "model_ok.pth")
    # 画图
    print(log)
    plt.plot(range(len(log)), [l[0] for l in log], label="acc")  # 画acc曲线
    plt.plot(range(len(log)), [l[1] for l in log], label="loss")  # 画loss曲线
    plt.legend()
    plt.show()
    return


# 加载训练好的模型，并对传入的其他真实样本做预测
def predict(model_path, input_vec):
    input_size = 6
    model = TorchModel(input_size)
    model.load_state_dict(torch.load(model_path))  # 加载训练好的权重
    #print(model.state_dict()) #查看模型的状态

    model.eval()  # 测试模式
    with torch.no_grad():  # 不计算梯度
        result = model.forward(torch.FloatTensor(input_vec))  # 模型预测
    for vec, res in zip(input_vec, result):
        print("输入：%s, 预测类别：%d, 概率值：%f" % (vec, round(float(res)), res))  # 打印结果


if __name__ == "__main__":
    main()
    test_vec = [[0.47889086,0.15229675,0.31082123,0.03504317,0.18920843,0.47889086],
                [0.94963533,0.5524256,0.95758807,0.95520434,0.84890681,0.94963533],
                [0.78797868,0.67482528,0.13625847,0.34675372,0.99871392,0.78797868],
                [0.1349776,0.59416669,0.92579291,0.41567412,0.7358894,0.1349776]]
    #使用训练好的模型做预测
    predict("model_ok.pth", test_vec)