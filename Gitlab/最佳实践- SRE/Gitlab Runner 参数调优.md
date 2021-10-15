# 背景说明
- 阅读此文档前请确保已经阅读[ Gitlab runner 前置知识](http://wiki.platform.mobiu.space/document/index?document_id=484 " Gitlab runner 前置知识")和 [Gitlab runner 安装](http://wiki.platform.mobiu.space/document/index?document_id=485 "Gitlab runner 安装")文档
- 在 Kubernetes 上构建的 Gitlab runner 与 GitLab CI 一起使用时，Kubernetes 执行程序将连接到集群中的 Kubernetes API，从而为每个 GitLab CI 作业创建一个 Pod
	- 此 Pod 至少由 build container，helper container 以及用于 .gitlab-ci.yml 或 value.yaml  文件中 service 定义的附加容器组成

# 操作详解
## Gitlab Runner 配置方式简介
- value.yaml 或 config.toml 文件
 - value.yaml 或 config.toml 文件都是 Gitlab Runner 的配置文件，config.toml 是新版本的配置文件，结构更加简单
 - 我司的线上 gitlab runner 当前采用的是 value.yaml 文件来对 gitlab runner 进行配置
- .gitlab-ci.yml
 - 在 .gitlab-ci.yml 中，可以全局地或者是针对单独的 job，配置 Runner 的 Git 行为，来获取 repository 存储库内容

## value.yaml 配置最佳实践
### 线上 Gitlab Runner 配置详解
- 线上 gitlab-runner 配置地址：[gitlab-runner 配置](https://gitlab.mobiuspace.net/mobiuspace/sre-team/kube-deploy-configure/-/blob/master/conf/infrastructure/gitlab/helm/general.yml)

```bash
# 镜像拉取的策略
imagePullPolicy: Always
# gitlab 地址
gitlabUrl: https://gitlab.mobiuspace.net/
# gitlab-runner 注册时用到的 token
runnerRegistrationToken: "6tW5_8mCPeLHsikbY_C4"
# 开启取消注册已注册的 runner 的功能
unregisterRunners: true
# 向 Pod 中运行的进程发送终止信号后，进程的存活时间（包括 kill 强行终止的情况）
terminationGracePeriodSeconds: 3600
# 限制可以同时运行的作业数，即最大并发数。最大数量是所有已定义的跑步者，0 并不意味着 unlimit
concurrent: 100
# 定义两次新 job 检查之间的间隔长度（以秒为单位）。默认值为3。如果设置为0以下，则使用默认值，轮询间隔
checkInterval: 30
# 开启 rba [ rbac 简介：https://kubernetes.io/docs/reference/access-authn-authz/rbac/ ]
rbac: 
  # 是否创建 rbac 服务账号
  create: true
  # 在整个集群范围内部署 job 容器，默认为 false
  clusterWideAccess: false 
metrics:
  enabled: true
# runner 的配置
runners:
  image: ubuntu:16.04
  imagePullSecrets: ["us-east-1-ecr-registry"]
  # 限制 GitLab 对新 job 的并发请求数量
  requestConcurrency: 100
  tags: "general"
  runUntagged: true
  # 使容器在特权模式下运行，不安全，建议设为 false
  privileged: true
  # 命名空间
  namespace: gitlab
  pollTimeout: 180
  outputLimit: 20480
  cache:
    ## General settings 分布式缓存
    cacheType: s3
    cachePath: "gitlab_runner"
	# 启用共享缓存
    cacheShared: true

    ## S3 settings
    s3ServerAddress: s3.amazonaws.com
    s3BucketName: mobiuspace-gitlab-runner
    s3BucketLocation: us-east-1
    s3CacheInsecure: false
    secretName: s3access

  # Build Container 配置
  builds:
    cpuLimit: 3
    memoryLimit: 15Gi
    cpuRequests: 1500m
    memoryRequests: 8000Mi

  # Service Container 配置
  services:
    cpuLimit: 1000m
    memoryLimit: 1000Mi
    cpuRequests: 100m
    memoryRequests: 100Mi

  # Helper Container 配置
  helpers:
    cpuLimit: 500m
    memoryLimit: 500Mi
    cpuRequests: 100m
    memoryRequests: 100Mi
    # image: gitlab/gitlab-runner-helper:x86_64-latest
resources: {}
  # limits:
  #   memory: 256Mi
  #   cpu: 200m
  # requests:
  #   memory: 128Mi
  #   cpu: 100m

# 节点亲和力
## 可以根据节点上的标签来限制 Pod 可以安排在哪些节点上进行调度
affinity:
  nodeAffinity:
  # 指定了将 Pod 调度到节点上必须满足的规则，只能将 Pod 放置在带有标签的节点上，如果节点上的标签在运行时发生更改，则该 pod 无法调度到该节点
    requiredDuringSchedulingIgnoredDuringExecution: # 硬要求
      nodeSelectorTerms:
      - matchExpressions:
        - key: eks.amazonaws.com/nodegroup
          operator: In
          values:
          - gitlab-runner
          - worker
    preferredDuringSchedulingIgnoredDuringExecution: # 软要求
    - weight: 60
      preference:
        matchExpressions:
        - key: eks.amazonaws.com/nodegroup
          operator: In
          values:
          - gitlab-runner

nodeSelector: {}
tolerations: []
hostAliases: []
podAnnotations:
  sidecar.istio.io/inject: false
```

### CPU / 内存优化
- 并发数配置过大，只有两个 runner 配置为 2 即可

```bash
concurrent: 100
requestConcurrency: 100
```
- cpu 和内存的限制分配过大
	- 构建容器的 cpu 和内存的限制，宿主机是 2 cpu 4G

```bash
builds:
    cpuLimit: 3
    memoryLimit: 15Gi
    cpuRequests: 1500m
    memoryRequests: 8000Mi
```

- Runner 默认情况下每执行一个 Job 都会重新拉取一次所需镜像，我们可把策略改为：镜像不存在时才拉取
	- 在 runner 的配置下 加上此配置

```bash
pull_policy = "if-not-present"
```

## .gitlab-ci.yml 配置参数详解

| 参数             | 含义                                                         | 备注                                                         |
| ---------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| script           | 由 runner 执行的 shell 脚本，是 job 中唯一必须的关键字参数   |                                                              |
| before_script    | 用于定义在所有 job 之前需要执行的命令，比如更新代码、安装依赖、打印调试信息等 | job 中的 before_script 和 after_script 的优先级高于全局配置的 |
| after_script     | 用于定义在所有 job 执行(即使失败)之后需要执行的命令，比如清空工作空间 |                                                              |
| stages           | 定义 pipeline 的全部阶段（stage），阶段内所有任务并行执行，全部执行成功开始下一阶段任务，任何阶段内任意 job 执行失败都会导致 pipeline 失败，所有stage、job 执行成功后 pipeline 会显示 pass 如果未定义 stages，则默认有 build、test、deploy 三个阶段 |                                                              |
| stage            | 定义 job 阶段，如果未定义 stage，则默认 test 阶段，处于相同阶段的 job 并行执行 |                                                              |
| variables        | 配置全局变量或者作业级的局部变量                             | 在下方做详细解释                                             |
| image            | 指定使用的 docker 镜像                                       |                                                              |
| services         | 指定使用的 docker 镜像服务                                   |                                                              |
| only             | 创建作业时，定义了哪些分支或标签的作业会运行                 | only 和 except  可同时使用；only 和 except 可使用正则表达式；only 和 except 允许指定用于过滤 forks 作业的存储库路径； only 和 except 可以使用特殊的关键字，如：branches、tags、api、piplines 等 |
| except           | 创建作业时，定义了哪些分支或标签的作业不会运行               | 同上                                                         |
| when             | when 关键字用于实现在 job 失败时或发生故障时的情况，可设置的值：on_success、on_failure、always、manual、delayed | on_success ：只有前面阶段的所有作业都成功时才执行，默认值；on_failure ：当前面阶段的作业至少有一个失败时才执行；always : 无论前面的作业是否成功，一直执行本作业；manual ：手动执行作业，作业不会自动执行，需要人工手动点击启动作业；delayed : 延迟执行作业，配合 start_in 关键字一起作用， start_in 设置的值必须小于或等于1小时，start_in 设置的值示例： 10 seconds / 30 minutes / 1 hour 前面的作业结束时计时器马上开始计时 |
| environment      | 用于定义 job 部署到特殊的环境中，没有该环境的话会自动创建    |                                                              |
| environment:name | 定义环境名称                                                 |                                                              |
| environment:url  | 是可选的，用于设置环境的URL地址的按钮                        | 在 Operations/environment 界面，通过点击按钮可以访问环境相应的URL地址 |
| cache            | cache 缓存机制，可以在全局设置或者每个作业中设置             |                                                              |
| cache:path       | 使用paths指令选择要缓存的文件或目录。路径是相对于项目目录（$CI_PROJECT_DIR）的，不能直接链接到项目目录之外 |                                                              |
| cache:key        | 定义作业之间缓存的亲和性，可以为所有作业使用单个缓存，按作业缓存，按分支缓存或适合您工作流程的任何其他方式，包括在不同作业甚至不同分支之间缓存数据 |                                                              |
| artifacts        | 用于指定在作业成功、失败、或者一直 pending 状态下时，应附加到 job 的文件或目录的列表，作业完成后，工件将被发送到 Gitlab,并可在 Gitlab UI 界面下载 |                                                              |
| artifacts:path   | 路径是相对于项目目录（$CI_PROJECT_DIR）的，不能直接在其外部链接 | 如果不传递，需要传递空数组：dependencies: []                 |
| coverage         | 可以从作业的输出 log 中提取代码覆盖率，仅支持正则表达式，字符串的前后必须使用/包含来表明一个正确的正则表达式规则，特殊字符串需要转义 |                                                              |

### variable 详解
- 定义全局变量或作业级的局部变量

##### GIT_STRATEGY
- 在 `.gitlab-ci.yml` 中，可以全局地或者是针对单独的 job，配置 Runner 的 Git 行为用于获取 repository 存储库内容

```bash
variables:
  GIT_STRATEGY: clone
```
- GIT_STRATEGY 有三种可能的值：clone / fetch / none
	- clone
		- 最慢的选择，为每个 job 从头开始克隆存储库，以确保本地工作副本始终是原创的，如果找到了现有的 worktree，git clone 策略会先将其删除，再进行克隆
	- fetch
		- 更快，它可以使用本地工作的副本，git fetch 用于检索上一个 job 运行后进行的提交
	- none
		- 重用了本地的工作副本，但跳过了通常由 Gitlab 完成的所有 Git 操作，也会跳过GitLab Runner的预克隆脚本（如果有的话），但使用该策略需要在 script 脚本中添加 fetch 和 checkout 命令

##### GIT_SUBMODULE_STRATEGY
- 当项目中需要包含别的项目代码时，可以使用 GIT_SUBMODULE_STRATEGY ，可以将别的项目作为本项目的子模块
- GIT_SUBMODULE_STRATEGY 需要在 .giltabmodules 中配置
- GIT_SUBMODULE_STRATEGY 可以有以下取值：
	- none：拉取代码时，子模块不会被引入
	- normal：只有第一级子模块会被引入
	- recursive：递归引入子模块的所有级

```bash
# 示例
# 本项目 https://gitlab.com/secret-group/my-project
# 依赖项目 https://gitlab.com/group/project
# 配置如下：
 [submodule "project"]
  path = project
  url = ../../group/project.git
```

##### GIT_CHECKOUT
- 控制 git checkout 的行为，可选的值：true / false，默认为 true

```bash
variables:
  GIT_STRATEGY: clone
  GIT_CHECKOUT: "false"
script:
  - git checkout -B master origin/master
```
- 如果设置为 true ，GitLab Runner 会检出本地工作副本并切换到当前修订版本分支上
- 如果设置为 false，则 Runner
	- 执行时 fetch-更新 repository 存储库并将工作副本保留在当前修订版上
	- 执行时 clone-克隆存储库，并将工作副本保留在默认分支上

##### GIT_CLEAN_FLAGS
- 控制 git clean 的行为，接受 git clean 命令的所有选项
- 如果 GIT_CLEAN_FLAGS ：
 - 未指定，git clean 标志默认为 -ffdx 删除当前目录下所有没有跟踪过的目录和文件
 - none，git clean 则不执行
 - 如果 GIT_CHECKOUT: "false" 则禁用 git clean

##### Git 获取额外的标志
- GIT_FETCH_EXTRA_FLAGS 用于控制 git fetch 的行为
- 如果 GIT_FETCH_EXTRA_FLAGS：
	- 未指定，git fetch 标志默认与--prune --quiet 一起使用
	- 给定值 none，git fetch 则仅使用默认标志执行

##### 浅克隆
- 通过指定深度来 fetch 和 clone ，可显著加快克隆速度
- Gitlab 12.0 版本之后，新项目默认 git depth 的值是 50
- GIT_DEPTH 的值不宜设置过小，因为可能会导致旧的提交无法运行

##### 自定义构建目录
- GitLab Runner 默认会把存储库克隆到 $CI_BUILDS_DIR 目录的唯一子路径中，但是某些项目可能需要特定目录中的代码，此时，可以通过指定 GIT_CLONE_PATH 变量来告诉运行程序目录
- 仅限于 GitLab Runner 在配置中启用 custom_build_dir 功能时，此功能才可以使用

```bash
variables:
  GIT_CLONE_PATH: $CI_BUILDS_DIR/project-name
```
##### Artifact and cache settings
- 可以指定 job 生成的归档文件的大小
 - 在速度较慢的网络上，较小档案的上传速度可能更快
 -  在不考虑带宽和存储的快速网络中，尽管归档文件较大，但使用最快的压缩率上传可能会更快

```bash
variables:
  # 指定多久打印一次仪表的传输速率
  TRANSFER_METER_FREQUENCY: "2s"

  # Use fast compression for artifacts，要调整的压缩比,为了使 GitLab Pages 能够 响应 HTTP Range请求,该参数应设为 fastest
  ARTIFACT_COMPRESSION_LEVEL: "fast"

  # 要调整的压缩比，Use no compression for caches
  CACHE_COMPRESSION_LEVEL: "fastest"
```

### 特殊的 YAML 功能
- 暂时禁用某个 job，可以在 job 名前，加一个（.），例如：
```bash
.hidden_job:
  script:
    - run test
```

- 锚点( ＆ )，别名( * )和合并( << )
	- 使用锚点和合并创建两个作业

```bash
# & 设置锚点名称为 job_definition
 .job_template: &job_definition
  image: ruby:2.1
  services:
    - postgres
    - redis
test1:
# << 合并，将锚点定义的模板内容复制到当前作业的当前位置来
# * 包含锚点的名称 job_definition
  <<: *job_definition
  script:
    - test1 project
test2:
  <<: *job_definition
  script:
    - test2 project
```