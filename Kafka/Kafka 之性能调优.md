## Kafka 之性能调优

### 1. 定位性能瓶颈

- 获取基线数据
- 分解端到端数据流延时分布
- 监控关键 JMX 指标
  - 请求延时
  - 网络线程池使用情况
  - 请求处理线程池使用情况

![image-20210609202403733](/Users/kevintttccc/Desktop/Technical Doc/Kafka/Kafka访问流程.png)

​	这六步当中你需要确定瓶颈在哪？怎么确定？——通过不同的JMX指标。

​	比如说 `步骤1` 是慢的，可能你经常碰到超时，你如果在日志里面经常碰到「request timeout」，就表示1是很慢的，此时要适当增加超时的时间。

​	如果2、3慢的情况下，则可能体现在磁盘IO非常高，导致往磁盘上写数据非常慢。

​	倘若是步骤4慢的话，查看名为remote-time的JMX指标，此时可以增加fetcher线程的数量。

​	如果5慢的话，表现为response在队列导致待的时间过长，这时可以增加网络线程池的大小。

​	6与1是一样的，如果你发现1、6经常出问题的话，查一下你的网络。

​	所以，就这样来分解整个的耗时。这是到底哪一步的瓶颈在哪，需要看看什么样的指标，做怎样的调优