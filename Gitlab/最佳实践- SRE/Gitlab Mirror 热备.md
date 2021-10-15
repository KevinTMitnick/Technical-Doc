# 背景说明
- 为什么要做热备份？
	- 避免对生产环境 Gitlab 的误操作，导致数据被删除，且备份数据不全
- 通过什么方式来做热备？
	- 使用 `Gitlab Remote Mirror` 功能，对生产的 Gitlab 的每个项目做热备
- 使用 Gitlab Mirror 时，触发数据数据同步的条件
	- 有新的 `commit` 或者 `force update` 才会触发同步
	- 新创建的 Gitlab 项目不会自动同步，需要通过 `监控脚本` 定时监控


# 操作环境
| 操作环境           | 说明       |
| ------------------ | ---------- |
| 生产 Gitlab 节点   | 作为主节点 |
| Gitlab Mirror 节点 | 热备节点   |

# 操作详解

## 第 1 步：创建备份 Gitlab
- 安装部署新的 gitlab 服务
	- 参考文档：[部署 Gitlab staging 环境](http://wiki.platform.mobiu.space/document/index?document_id=453)

## 第 2 步：在备份 Gitla 创建想用用户组/子用户组、项目名
- 注意事项
	- 用户组 / 子用户组、项目名、项目路径必须和生产 Gitlab 保持一致
- 在备份 Gitlab 上创建对应的：`用户组 / 子用户组`，`项目名`，python 脚本如下：

```python
import gitlab

'''
说明: 从 prod 环境的 gitlab 获取 group 和 subgroup 名称，在 gitlab mirror 上创建对应的关系组
'''

prod_gitlab = gitlab.Gitlab('https://gitlab.mobiuspace.net', private_token='fmdhG4mRsCDFFXzxSdts')
backup_gitlab= gitlab.Gitlab('https://gitlab-backup.mobiuspace.net/', private_token='9Yukbhz-ezRCyNNoAqfU')

def create_group():
    group = backup_gitlab.groups.create({'name': 'Mobiuspace', 'path': 'mobiuspace'})

def get_parent_groupId():
    groups = backup_gitlab.groups.list()
    for i in groups:
        if i.name == 'Mobiuspace':
            parent_id = i.id    # id = 8

def create_subgroup():
    group = prod_gitlab.groups.list()
    for i in group:
        group_id = i.id
        group_path = i.path
        backup_gitlab.groups.create({'name': i.name, 'path': i.path, 'parent_id': 8})
```

- 在备份 Gitlab 创建对应的项目名称

```python
import gitlab

prod_gitlab = gitlab.Gitlab('https://gitlab.mobiuspace.net', private_token='fmdhG4mRsCDFFXzxSdts')
backup_gitlab = gitlab.Gitlab('https://gitlab.staging.mobiuspace.net/', private_token='9Yukbhz-ezRCyNNoAqfU')

# 在 Prod Gitlab 上, 根据 「group_name」 获取对应组下所有的 「项目名称」
def get_project_of_group(group_name):
    group_project_list = []
    
    group_id = prod_gitlab.groups.list(search=group_name)[0].id
    for page in range(1, 30):
        projects = prod_gitlab.projects.list(page=page)
        for project in projects:
            if project.namespace['id'] == group_id:
                group_project_list.append(project.name)
    return group_project_list     

# 在 Backup-Gitlab 实例上在对应的「组」下创建对应项目
def create_project(project_list, team_id):
    for project in project_list:
        backup_gitlab.projects.create({'name': project, 'namespace_id': team_id})


# 示例：获取 sre-team 组下所有项目，然后在 Backup-Gitlab 上创建
# group_list=['sre-team', 'be-team', 'alg-team', 'fe-team', 'and-team', 'qa-team', 'data-team']
# project_list = get_project_of_group(group_name='sre-team')
mirror_group_dict = {'sre-team': 16,'be-team': 11, 'alg-team': 9, 'fe-team': 13, 'and-team': 10, 'qa-team': 15, 'data-team': 12}
for group_name in mirror_group_dict:
    project_list = get_project_of_group(group_name=group_name)
    create_project(project_list=project_list, team_id=mirror_group_dict[group_name])
```

## 第 3 步：为生产 Gitlab 所有项目创建 Remote Mirror
- 给生产 Gitlab 的项目创建 `Remote Mirror`

```python
import gitlab

prod_gitlab = gitlab.Gitlab('https://gitlab.mobiuspace.net', private_token='fmdhG4mRsCDFFXzxSdts')
backup_gitlab = gitlab.Gitlab('https://gitlab-backup.mobiuspace.net/', private_token='9Yukbhz-ezRCyNNoAqfU')

# 在 Prod Gitlab 上, 根据 「group_name」 获取对应组下所有的 「项目名称」
def get_project_of_group(group_name):
    group_project_list = []
    group_id = prod_gitlab.groups.list(search=group_name)[0].id
    for page in range(1, 30):
        projects = prod_gitlab.projects.list(page=page)
        for project in projects:
            if project.namespace['id'] == group_id:
                group_project_list.append(project.name)
    return group_project_list

# 根据「group_name」名称，为组下所有的 Project 创建 Remote Mirror
def create_mirror_of_group(group_name, project_list):
    for project_name in project_list:
        mirror_url = f'https://root:9Yukbhz-ezRCyNNoAqfU@gitlab-backup.mobiuspace.net/mobiuspace/{group_name}/{project_name}.git'
        for page in range(1, 30):
            projects = prod_gitlab.projects.list(page=page)
            for project in projects:
                if project.name == project_name:
                    print(mirror_url)
                    mirror = project.remote_mirrors.create({'url': mirror_url, 'enabled':True})

group_list=['sre-team', 'be-team', 'alg-team', 'fe-team', 'and-team', 'qa-team', 'data-team']

# 示例: 给 Prod-gitlab 下所有的项目创建 Remote Mirror
# project_list=get_project_of_group('sre-team')
# create_mirror_of_group(group_name='sre-team', project_list=project_list)

for group_name in group_list:
    project_list=get_project_of_group(group_name)
	create_mirror_of_group(group_name=group_name, project_list=project_list)
````
## 第 4 步：验证
- 首先，在生产 Gitlab 自己的项目提交一个新的 `commit`
- 然后，登录备份 Gitlab 查看项目是否已经通过过来
	- 登录地址：https://gitlab-backup.mobiuspace.net/ 

# 新项目的监控脚本
- 监控生产 Gitlab 上新创建的项目
- 为新项目在 `Remote Mirror`

```python
import gitlab

"""
说明:
    1、监控 Prod 环境的 Gitlab 是否有新的项目创建
    2、有则获取项目信息, 然后到 gitlab mirror 上创建对应的项目
    3、配置新项目的 remote mirror，进行同步
"""

prod_gl = gitlab.Gitlab('https://gitlab.mobiuspace.net', 'fmdhG4mRsCDFFXzxSdts')
mirror_gl = gitlab.Gitlab('https://gitlab-backup.mobiuspace.net/', private_token='9Yukbhz-ezRCyNNoAqfU')

# 获取新的项目
def compare_project():
    prod_project_set = set()
    mirror_project_set = set()

    for page in range(1,100):
        projects = prod_gl.projects.list(page=page)
        for project in projects:
            prod_project_set.add(project.name)

    for page in range(1,100):
        projects = mirror_gl.projects.list(page=page)
        for project in projects:
            mirror_project_set.add(project.name)

    new_project = prod_project_set - mirror_project_set
    return new_project


# 查询 Project 对应的 team
def get_project_team(new_projects):
    project_and_team = []
    for name in new_projects:
        project = prod_gl.projects.list(search=name)
        for i in project:
            tmp_map = {'project': name, 'team_name': i.namespace['path']}
            project_and_team.append(tmp_map)
    return project_and_team

# 在 Gitlab mirror 上创建新的 Project
def create_project(projects_info):
    mirror_group_id = {'sre-team': 16,'be-team': 11, 'alg-team': 9, 'fe-team': 13, 'and-team': 10, 'qa-team': 15, 'data-team': 12}
    for project in projects_info:
        mirror_gl.projects.create({'name': project['project'], 'namespace_id': mirror_group_id.get(project['team_name'])})

# 为新的 Project 创建 Remote Mirror
def create_project_mirror(project_info):
    for project_name in project_info:
        mirror_url = f'https://root:9Yukbhz-ezRCyNNoAqfU@gitlab-backup.mobiuspace.net/mobiuspace/{project_name["team_name"]}/{project_name["project"]}.git'
        for page in range(1, 100):
            projects = prod_gl.projects.list(page=page)
            for project in projects:
                if project.name == project_name['project']:
                    mirror = project.remote_mirrors.create({'url': mirror_url, 'enabled':True})

new_project = compare_project()
project_info = get_project_team(new_project)
create_project(project_info)
create_project_mirror(project_info)
```