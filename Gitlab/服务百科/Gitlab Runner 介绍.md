# 背景说明
- Gitlab CI 和 Gitlab Runner 的关系
	- GitLab CI 最大的作用是管理各个项目的构建状态，运行构建任务这种比较消耗资源的事情由 GitLab Runner 来做处理。
	- GitLab Runner 是单独运行在 EKS 集群中的。

# 正文介绍
## Gitlab Runner 简介
- GitLab Runner 是与 GitLab CI / CD一起使用的应用程序，用于在 pipeline 中运行作业，用 Go 语言编写

### Gitlab Runner 的类型
- Shared runners 共享运行器
- Group runners 组运行器
- Specific runners

#### Shared runners

##### Shared runners 的适用场景
- Gitlab 实例中每个项目都可以使用共享的运行器
- 当您有多个要求相似的工作时，建议使用共享运行器。可以用少数的运行器运行多个项目，而不是让多个运行器在许多项目上空闲下来
- 管理员还可以为每个组配置最大的共享运行器 [管道分钟数](https://docs.gitlab.com/ee/user/admin_area/settings/continuous_integration.html#shared-runners-pipeline-minutes-quota "管道分钟数")

##### Shared runners 如何工作
- 共享的运行器通过合理使用队列来处理 job，此队列可防止项目创建数百个 job，并占用所有可用的共享运行器资源
- 合理使用队列算法，根据在共享运行程序上运行的 job 量最少的项目来分配 Runner

##### 举例：说明合理使用算法是如何工作的
- 如果这些 job 在队列中：

 - 项目 1 的 job 1
 - 项目 1 的 job 2
 - 项目 1 的 job 3
 - 项目 2 的 job 4
 - 项目 2 的 job 5
 - 项目 3 的 job 6

- 合理使用算法按以下顺序分配 job 情况 1：

 - 首先选择 job 1，因为它在没有正在运行的 job 的项目（即所有项目）中具有最低的 job 编号
 - 接下来是 job 4，因为 4 现在是没有正在运行的 job 的项目中最低的 job 编号（项目 1 正在运行 job）
 - 接下来是 job 6，因为 6 现在是没有正在运行的 job 的项目中最低的 job 编号（项目 1 和 2 都有正在运行的 job）
 - 接下来是 job 2，因为在运行的 job 数量最少的项目中（每个项目都有 1），它是最低的 job 编号
 - 接下来是 job 5，因为项目 1 现在有 2 个正在运行的 job，而 job 5 是项目 2 和项目 3 之间剩余的最低编号
 - 最后是 job 3…，因为这是剩下的唯一 job

- 合理使用算法按以下顺序分配 job 情况 2：
 - 首先选择 job 1，因为它在没有正在运行的 job 的项目（即所有项目）中具有最低的 job 编号
 - 完成了 job 1
 - 接下来是 job 2，因为完成 job 1 后，所有项目都再次运行 0 个 job，而 2 是最低的可用 job 编号
 - 接下来是 job 4，因为在项目 1 运行 job 的情况下，项目 4 在没有 job 运行的项目（项目 2 和 3）中是最低的
 - 完成了 job 4
 - 接下来是 job 5，因为完成了 job 4，所以项目 2 没有再次运行的 job
 - 接下来是 job 6，因为项目 3 是剩下的唯一一个没有正在运行的 job 的项目
 - 最后，我们选择Job 3…，因为它是剩下的唯一 job

#### Group runners
##### Group runners 适用场景
- 当我们希望组中的所有项目都可以访问一组运行器时，建议使用「组运行器」。
- 组运行器通过使用先进先出（[FIFO](https://en.wikipedia.org/wiki/FIFO_(computing_and_electronics) "FIFO")）队列来处理 job。

##### 组运行器管理者
- 组运行器管理者的使用在 Gitlab 13.2 中引入，可以用来查看和管理组

#### Specific runners
##### Specific runners 适用场景
- 当你想让一个特定的项目只使用特定的运行器时，建议使用 Specific runners
 - 有特定要求的 job，例如需要部署凭据的 job
 - 与其他 CI 参与者分开可以受益于 CI 活动的项目
- 一个特定的运行器可以供多个项目使用，但必须为每个项目明确启用特定的运行器
- 特定运行器也是通过使用先进先出（[FIFO](https://en.wikipedia.org/wiki/FIFO_(computing_and_electronics "FIFO")）队列来处理 job

### Gitlab Runner 性能优化
#### 设定 Gitlab Runner 的最大作业超时
可以设定 Gitlab Runner 的最大 job 超时，防止运行器被具有较长超时的项目困住
- 对于每个 Runner，可以指定最大 job 超时时间，如果这个时间小于项目规定的超时时间，则 Runner 的优先级更高，反之则按照项目规定的超时时间
 - Runner 设置的超时时间为 2 小时，项目超时时间为 24 小时，如果运行时间过长，该 job 将在两小时后超时
  - Runner 设置的超时时间为 24 小时，项目超时时间为 2 小时，如果运行时间过长，该 job 将在两小时后超时

#### 使用标签限制使用 Runner 的作业数量
- 标签可以用来区分不同类型的 job，这里需要注意
 - GitLab CI 标签与 Git 标签是不同的，GitLab CI 标签与跑步者相关联，Git 标签与提交相关联
- 通过为运行器标记其可以处理的 job 类型，可以确保共享的运行器仅运行他们有能力运行的 job
- 当注册了一个 Runner 时，它默认只会执行有标签的 job
 - 当你的工作无法执行时，可以查看一下该工作是否有标签，要让 Runner 可以选择无标签的 job，需要在项目的 settings 更改 Runner 的配置，具体操作查看[官方文档](https://docs.gitlab.com/ee/ci/runners/#types-of-runners "官方文档")

### Gitlab Runner 安全优化
#### 防止跑步者泄露敏感信息
- 当运行器受到保护时，该运行器仅选择在受保护分支或受保护标签上创建的 job，而忽略其他 job
- 可在项目的 setting --> CI / CD --> Runner 中设置
- 具体步骤可参考[官方文档](https://docs.gitlab.com/ee/ci/runners/#types-of-runners "官方文档")

#### 重置项目的跑步者注册令牌
- 如果您认为某个项目的注册令牌已公开，则应将其重置
 - 令牌可用于为该项目注册其他跑步者。然后，可以使用该新运行程序来获取秘密变量的值或克隆项目代码
 - 具体操作步骤可参考[官方文档](https://docs.gitlab.com/ee/ci/runners/#types-of-runners "官方文档")