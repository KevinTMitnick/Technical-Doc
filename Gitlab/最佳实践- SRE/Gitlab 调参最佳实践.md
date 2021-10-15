# 背景说明
- 为什么要参数调优？
	- Gitlab 是一个重量级的代码托管平台，启动会占用大量资源，比例：CPU、内存，所有有必要对 Gitlab 进行参数调优。

# 操作详解
## Gitlab 配置介绍
- Gitlab 线上服务 gitlab.rb 中关于各个模块的配置

```bash
external_url 'http://gitlab.mobiuspace.net'
gitlab_rails['gitlab_email_from'] = "noreply@dayuwuxian.com"
gitlab_rails['gitlab_email_reply_to'] = 'gitlab+noreply@dayuwuxian.com'
gitlab_rails['monitoring_whitelist'] = ['127.0.0.0/8', '172.29.1.182']
gitlab_rails['omniauth_enabled'] = true
  {
    "name" => "google_oauth2",
    "app_id" => "925225479470-1gs722v9h3fdh6k40n0lmg9cgbu1eog9.apps.googleusercontent.com",
    "app_secret" => "mQKMHxqTwKLbxUJN_gcHctiW",
    "args" => { "access_type" => "offline", "approval_prompt" => '' }
    "args" => { "scope" => "api" }
  },
]
gitlab_rails['rate_limit_requests_per_period'] = 10000
gitlab_rails['rate_limit_period'] = 1
gitlab_rails['db_adapter'] = "postgresql"
gitlab_rails['db_encoding'] = 'utf8'
gitlab_rails['db_username'] = 'gitlab'
gitlab_rails['db_password'] = 'zqPmrdzW3a2g7ch81'
gitlab_rails['db_host'] = 'gitlab-test.copacaoqgakl.us-east-1.rds.amazonaws.com'
gitlab_rails['db_port'] = 5432
gitlab_rails['smtp_enable'] = true
gitlab_rails['smtp_address'] = "email-smtp.us-east-1.amazonaws.com"
gitlab_rails['smtp_port'] = 587
gitlab_rails['smtp_user_name'] = "AKIAJAOWLQHUXW7STMGA"
gitlab_rails['smtp_password'] = "AmQ5bF4iCA2lhwTJSEW4Y1xYL18zVXGbC5PLieRWyq4C"
gitlab_rails['smtp_domain'] = "dayuwuxian.com"
gitlab_rails['smtp_authentication'] = :login
gitlab_rails['smtp_enable_starttls_auto'] = true
gitlab_workhorse['enable'] = true
gitlab_workhorse['prometheus_listen_addr'] = "0.0.0.0:9229"
gitlab_workhorse['api_queue_limit'] = 100
gitlab_workhorse['api_queue_duration'] = "30s"
gitlab_workhorse['api_ci_long_polling_duration'] = "60s"
user['git_user_email'] = "gitlab+noreply@dayuwuxian.com"
unicorn['enable'] = true
unicorn['worker_processes'] = 6
unicorn['exporter_enabled'] = true
unicorn['exporter_address'] = "0.0.0.0"
unicorn['exporter_port'] = 8083
puma['enable'] = false
puma['ha'] = true
puma['worker_timeout'] = 60
puma['worker_processes'] = 3
puma['min_threads'] = 1
puma['max_threads'] = 4
puma['exporter_enabled'] = false
puma['exporter_address'] = "0.0.0.0"
puma['exporter_port'] = 8083
sidekiq['shutdown_timeout'] = 4
sidekiq['concurrency'] = 25
sidekiq['metrics_enabled'] = true
sidekiq['listen_address'] = '0.0.0.0'
sidekiq['listen_port'] = 8082
postgresql['enable'] = false
redis['maxmemory'] = "100mb"
nginx['enable'] = true
nginx['client_max_body_size'] = '250m'
nginx['redirect_http_to_https'] = false
nginx['redirect_http_to_https_port'] = 80
nginx['ssl_verify_client'] = "off"
nginx['custom_gitlab_server_config'] = "proxy_buffering off;"
nginx['proxy_set_headers'] = {
 "Host" => "$http_host_with_default",
 "X-Real-IP" => "$remote_addr",
 "X-Forwarded-For" => "$proxy_add_x_forwarded_for",
 "X-Forwarded-Proto" => "https",
 "X-Forwarded-Ssl" => "on",
 "Upgrade" => "$http_upgrade",
 "Connection" => "Keep-Alive"
}
nginx['status'] = {
 "enable" => true,
 "listen_addresses" => ["0.0.0.0"],
 "fqdn" => "localhost",
 "port" => 8060,
 "vts_enable" => true,
 "options" => {
 }
}
pages_external_url "http://pages.mobiuspace.net/"
gitlab_pages['enable'] = true
gitlab_pages['log_verbose'] = true
gitlab_pages['listen_proxy'] = "localhost:8090"
gitlab_pages['inplace_chroot'] = false
pages_nginx['enable'] = true
prometheus['enable'] = false
node_exporter['enable'] = true
node_exporter['listen_address'] = '0.0.0.0:9100'
redis_exporter['enable'] = true
redis_exporter['listen_address'] = '0.0.0.0:9121'
postgres_exporter['enable'] = true
postgres_exporter['listen_address'] = '0.0.0.0:9187'
gitlab_exporter['enable'] = true
gitlab_exporter['listen_address'] = '0.0.0.0'
prometheus_monitoring['enable'] = false
grafana['enable'] = false
gitaly['enable'] = true
gitaly['prometheus_listen_addr'] = "0.0.0.0:9236"
praefect['prometheus_listen_addr'] = "0.0.0.0:9652"
sidekiq_cluster['enable'] = false
sidekiq_cluster['min_concurrency'] = 1
sidekiq_cluster['queue_groups'] = [
  "process_commit,post_receive",
  "gitlab_shell"
]
sidekiq_cluster['negate'] = true
```

## Gitlab 调参最佳实践
### 优化 1：启用HTTPS
- 默认情况下，Omnibus GitLab 不使用 HTTPS。要启用 HTTPS，有两种选择：
 - 使用 [Let's Encrypt](https://letsencrypt.org/zh-cn/) 进行免费和自动化的 HTTPS
 - 使用自己的证书手动配置 HTTPS

####  Let's Encrypt 是什么？
- Let's Encrypt 是一个非盈利的证书颁发机构，向 2.4 亿个网站提供 TLS 证书，[官方地址](https://letsencrypt.org/zh-cn/)
- AWS 是其赞助商之一，因此我们通过 AWS 申请的证书，应选用 Let's Encrypt 方式启用 HTTPS

####  Let's Encrypt 启用 HTTPS 
- 运行验证的 Let's Encrypt 服务器将需要访问 Gitlab 服务器的 80 和 443 端口，当前验证不适用于非标准端口
- 支持  Let's Encrypt 的配置

```bash
letsencrypt['enable'] = true                                   # GitLab 10.5 and 10.6 require this option
external_url "https://gitlab.example.com"            # Must use https protocol
letsencrypt['contact_emails'] = ['foo@email.com']   # 可以不设置，因为 AWS CM 会自动更新快要过期的证书
```
- 问题
	- external_url 不用 https 且 另外两项配置也去掉，证书的配置仍然生效，这是为什么

### 优化 2：Gitlab 内存消耗过大，如何进行参数优化
- 描述
	- 使用 gitlab 后，发现服务器内存居高不下，使用 top 命令查看内存消耗，发现服务 gitlab 消耗资源过多，且开启进程数过多
- 解决
	- 调整进程数和超时时间
	  - Gitlab 官方建议的进程数是 CPU 核数 + 1，以提高服务器的响应速度，但如果 CPU 核数过大，就需要对该参数进行调整了
	  - 如果进程数过多，假设有 30 个进程，一个进程消耗 500 MB 内存，将会有 15 G 内存的消耗，需要适当减少进程数，降低内存使用率
	  - 为了使 Web 正常工作，worker_processes 最低要求为2，低于 2 可能会卡死，原因请参考[官方提供的 issues 文档](https://gitlab.com/gitlab-org/gitlab/-/issues/14546 "官方提供的 issues 文档")

```bash
unicorn['worker_processes'] = 3
unicorn['worker_timeout'] = 60   #超时时间默认为 60
# 减少 unicorn 内存使用
unicorn['worker_memory_limit_min'] = "400 * 1 << 20" # 可从 400 减到 200
unicorn['worker_memory_limit_max'] = "600 * 1 << 20" # 可从 600 减到 300
```
- 降低sidekiq中的并发级别
	- 没有进行太多提交时，可适当降低并发级别

```bash
sidekiq['concurrency'] = 15 #25 is the default
```
- 减少postgres数据库缓存
	 - 如果使用了 Gitlab 默认的 PostgreSQL，建议做以下优化

```bash
# 减小数据库缓存，默认 256，可适当调小
postgresql['shared_buffers'] = "256MB" 
# 减小数据库并发数
postgresql['max_worker_processes'] = 8
```
- 禁用普罗米修斯监控

```bash
prometheus_monitoring['enable'] = false
```

### 优化 3：sidekiq 模块参数优化
- sidekiq_cluster 的配置就是起多个 sidekiq 进程，在 GitLab 13.0和更高版本中，默认运行 Sidekiq 群集，计划在GitLab 14.0中删除直接运行Sidekiq

```bash
sidekiq_cluster['enable'] = false
sidekiq_cluster['min_concurrency'] = 1 #多线程的配置
sidekiq_cluster['queue_groups'] = [
  "process_commit,post_receive",
  "gitlab_shell"，
  # '*' 代表所有队列
]
sidekiq_cluster['negate'] = true
# sidekiq['interval'] = 5  告诉其他进程多久检查一次排队的作业
```

### 优化 4：gitlab_workhorse 模块参数优化

```bash
gitlab_workhorse['enable'] = true
gitlab_workhorse['prometheus_listen_addr'] = "0.0.0.0:9229" #禁止 prometheus 的配置，使用外部的 prometheus 的配置
gitlab_workhorse['api_queue_limit'] = 100
gitlab_workhorse['api_queue_duration'] = "30s"
gitlab_workhorse['api_ci_long_polling_duration'] = "60s"

```

###  优化 5：Nginx 模块配置参数优化
```bash
nginx['client_max_body_size'] = '250m'
```
gitlab comment 中上传附件时，允许的最大文件大小，超过该数值会报错 413 Request Entity Too Large，可参考[官方文档](https://docs.gitlab.com/ee/user/admin_area/settings/account_and_limit_settings.html#413-request-entity-too-large "官方文档")

### 优化 6：速率限制
```bash
gitlab_rails['rate_limit_requests_per_period'] = 10000
gitlab_rails['rate_limit_period'] = 1

```

### 其他配置
- 使用外部 Prometheus 服务器

```bash
# 禁用捆绑的Prometheus
prometheus['enable'] = false
prometheus_monitoring['enable'] = false
grafana['enable'] = false
# 将每个捆绑服务的导出器设置为侦听网络地址
node_exporter['enable'] = true
node_exporter['listen_address'] = '0.0.0.0:9100'
# Rails nodes
gitlab_exporter['enable'] = true
gitlab_exporter['listen_address'] = '0.0.0.0'
# Sidekiq nodes
sidekiq['listen_address'] = '0.0.0.0'
sidekiq['listen_port'] = 8082
# Redis nodes
redis_exporter['enable'] = true
redis_exporter['listen_address'] = '0.0.0.0:9121'
# PostgreSQL nodes
postgres_exporter['enable'] = true
postgres_exporter['listen_address'] = '0.0.0.0:9187'
# Gitaly nodes
gitaly['enable'] = true
gitaly['prometheus_listen_addr'] = "0.0.0.0:9236"
# 将Prometheus服务器IP地址添加到监视IP白名单
gitlab_rails['monitoring_whitelist'] = ['127.0.0.0/8', '172.29.1.182']
# 在所有GitLab Rails（Puma / Unicorn，Sidekiq）服务器上，设置Prometheus服务器IP地址和监听端口
gitlab_workhorse['prometheus_listen_addr'] = "0.0.0.0:9229" #官方推荐 gitlab_rails['prometheus_address'] = "0.0.0.0:9229"

# 要抓取NGINX指标，还必须配置NGINX以允许Prometheus服务器IP
nginx['status'] = {
 "enable" => true,
 "listen_addresses" => ["0.0.0.0"],
 "fqdn" => "localhost",
 "port" => 8060,
 "vts_enable" => true,
 "options" => {
 }
}
```

