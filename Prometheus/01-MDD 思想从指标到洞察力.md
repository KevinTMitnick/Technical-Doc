## 什么是 MDD

​	MDD（Metrics-Driven Development）主张整个应用开发过程由指标驱动，通过实时指标来驱动快速、精确和细粒度的软件迭代

## MDD 关键原则

- 将 `指标`  分配给指标所有者（业务、应用、基础架构等）
  - 对软件研发人员来说，可以实时感知应用各项指标、聚焦应用优化
- 创建关联指标，并关联趋势
  - 对运维人员来说，可以实时感知系统各项指标、快速定位问题。
- 制定决策时使用的指标
  - 对产品经理、商务人士来说，可以实时掌控业务各项指标，通过数据帮助自己做出决策

## MDD 分层（主要 3 层）

- Infrastructure/System Metrics：如服务器状态、网络状态、流量等；
- Service/Application Metrics：如每个API耗时、错误次数等，可以分为中间件监控、容器监控（Nginx、Tomcat）等
- Business Metrics：运营数据或者业务数据，比如单位时间订单数、支付成功率、A/B测试、报表分析等

## 指导实践的 3 大监控方法论

#### Google 的四大黄金指标

- Latency：延迟
- Traffic：流量
- Errors：错误数
- Saturation：饱和度

#### Netflix的 USE 方法

- Utilization：使用率
- Saturation：饱和度
- Errors：错误数

#### Weave Cloud 的 RED 方法

- Rate：每秒接收的请求数量
- Errors：每秒失败的请求数
- Duration：每个请求所花费的时间，用时间间隔表示



