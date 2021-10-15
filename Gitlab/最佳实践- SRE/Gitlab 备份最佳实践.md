# 背景说明
- 由于误操作导致与 Gitlab 相关的文件不仅是配置文件全部被删除，为防止类似情况再次发生，现给 gitalb 服务进行备份
- 线上 Gitlab 环境和 Gitlab staging 环境均使用 Omnibus 软件包安装的 GitLab
	- 具体可查看 [部署 Gitlab staging 环境](http://wiki.platform.mobiu.space/document/index?document_id=453 "部署 gitlab staging 环境")
- 提示
	- 本文档参考 [Gitlab 官方文档](https://docs.gitlab.com/ee/raketasks/backup_restore.html#storing-configuration-files "gitlab 官方文档")说明，在 gitlab staging 环境进行实验

# 操作详解
## 第 1 步：备份说明
- 备份命令

```shell
sudo gitlab-backup create
```

 - 备份的内容包括：
 	- 该备份命令不会备份任何配置文件 ssl 证书或系统文件，这些均需单独备份

| 备份项                      | 解释                                                        | 备注                                                         |
| --------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| Database                    | 数据库备份                                                  | 备份 gitlab 本身自带的数据库，但目前我司已将数据库迁移到 AWS 的 RDS，且数据库有专门的备份方案（起快照） |
| Attachments                 | 附件备份                                                    |                                                              |
| Git repositories data       | Git 代码库数据备份                                          |                                                              |
| CI/CD job output logs       | 服务的 CI/CD 时，job 的输出日志                             |                                                              |
| CI/CD job artifacts         | 用于指定在 job 成功或失败时，应附加到作业的文件和目录的列表 |                                                              |
| LFS object                  | LFS 对象                                                    | Git Large File Storage (LFS) ,大文件存储功能,可用于处理项目中的大文件，在 git 中只会记录对此大文件的引用，不会将其加入 .git 文件夹中，使得项目体积不会猛增， checkout 和 add 时速度更快。LFS 合适用于 psd，视频等 |
| Container Registry images   | Gitlab 容器注册表备份                                       | 通过将 Docker 容器注册表集成到 GitLab中，每个GitLab项目都可以拥有自己的空间来存储其 Docker 映像 |
| GitLab Pages content GitLab | 页面内容备份                                                |                                                              |
| Snippets                    | 代码段备份                                                  | Gitlab 的 Snippets 功能可以保存、分享自己常用的代码片段，比自己留在本地电脑上要方便很多，而且能发挥这些片段的最大价值 |
| Group wikis                 | wiki 备份                                                   |                                                              |


## 需单独备份的文件
- /etc/gitlab/gitlab-secrets.json
- /etc/gitlab/gitlab.rb

## 备份的默认存储路径
- 备份的默认存储路径：`/var/opt/gitlab/backups`
- 备份文件不能存在本地，防止误删，可将其存储到 S3
	- 具体配置参考官方文档

## 备份存档权限
- 编辑 `/etc/gitlab/gitlab.rb`

```bash
gitlab_rails['backup_archive_permissions'] = 0644
   sudo gitlab-ctl reconfigure
```

## 编写定时任务进行每日备份
 ```bash
 sudo su -
 crontab -e
 0 2 * * * /opt/gitlab/bin/gitlab-backup create CRON=1
 # CRON=1 将指示备份脚本隐藏所有进度输出，可减少 Cron 垃圾邮件
 ```

## 限制备份文件的寿命
- 编辑`/etc/gitlab/gitlab.rb`

```bash
 gitlab_rails['backup_keep_time'] = 604800 # 只保留近7天的备份
 sudo gitlab-ctl reconfigure
```

## 第 2 步：恢复介绍
- 恢复的先决条件
	- 必须要先安装 Gitlab，并与之前版本保持一致
	- 检查 Gitlab 的状态

```shell
sudo gitlab-ctl status
```

# 参考文档
- 故障恢复参考文档
	- [Gitlab 数据误删除](http://wiki.platform.mobiu.space/document/index?document_id=954)
	- 