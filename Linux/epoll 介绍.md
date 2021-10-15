## 1. 内容

- Linux 网络服务器种类
- 多路复用介绍
- Epoll 之多路复用缺点
- Epoll 实现原理

### 1.1 种类

### 1.2 多路复用介绍

#### 1.2.1 select

`模型图`

![企业微信截图_ee033544-0aea-474d-874b-15d09bf1f337](/Users/kevintttccc/Desktop/Technical Doc/Linux/select 模型.png)

`优缺点`：

优点：

缺点：

- 最大并发数限制，由于一个进程打开所有的 `fd` 是有限制的，由「FD_SIZE」设置，默认是 1024/2048，因此 select 模型的最大并发数就被限制了（poll 模型克服了这个缺点）；
- 效率问题，每次进行 select 调用都会「线性扫描（循环）」全部 `fd 集合`，这样效率就会成线性下降；
- 「内核态」 -->  「用户态」的内存 copy 问题，select 在解决将 fd 消息传递给用户空间时采用了内存拷贝的方式，这样处理效率不高。

#### 1.2.2 poll

​		相比于 `select`  模型，poll 仅仅取消了「文件描述符表」的长度限制，仍然使用「轮训机制」和「内核态」到「用户态」的 copy

#### 1.2.3 epoll

##### Epoll 的提出

- 一种「通知机制」；
- 所支持的文件描述符上限时整个系统最大可以打开的文件数据。
  - 例如：1GB 内存大小的机器上，这个限制大概为 10 万左右；
- 每个 fd 上面都有 `callback()` 回调函数，只有活跃的 socket 才会主动去调用 `callback()` 函数，其他 `idle` 状态的 socket 则不会；
- 通过「内核」与「用户空间」 `mmap` 同一块内存来实现。

##### epoll 实现

- 就绪事件链表（rdllink）+ 红黑树 实现
  - 「红黑树」通过查询「事件链表」中的成员，根据 `fd` 读取其中的 `event 事件`，然后做相应的处理。

​	`eventpoll`

```c++
+ lock
+ mtx
+ wq
+ poll_wait
+ rdllist		# rbr 中每个节点都是基于 「epitem」结构中 rdllink 的成员
+ rbr				# rbr 中的每个节点都是基于「epitem」结构中的 rbn 成员
+ ovflist
+ user
```

`epitem`

```c++
+ rbn
+ rdllink
+ next
+ ffd
+ nwait
+ pwqlist
+ ep
+ fllink
+ event
```

##### epoll 的 api

`int epoll_create(int size)`

- 调用 `epoll_create` 方法来创建一个 epoll 句柄；
- 当创建好 「epoll 句柄」之后，它就会返回这个 fd 值。  当使用完 epoll 后，必须调用 `close()` 函数进行关闭，否则会导致：fd 被消耗怠尽

```c++
#include <sys/epoll.h>
// 创建「红黑树」跟节点，return：epfd
int epoll_create(int size);


// 
int epoll_pwait(int epfd, struct epoll_event *events,
                int maxevents, int timeout,
                const sigset_t *sigmask);
```

`epoll_ctl`

```c++
#include <sys/epoll.h>

// 控制 epoll 的属性
int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event);
```

- epfd：`epoll_create` 返回的「文件句柄」，红黑树树根；
- op：表示动作类型，有三个宏来表示，来操作红黑树的节点的动作
  - EPOLL_CTL_ADD：注册新的 fd 到 epfd 中
  - EPOLL_CTL_MOD：修改已经注册的 fd 监听的 event
  - EPOLL_CTL_DEL：从 epfd 中删除一个 fd
- fd：需要监听的 fd，红黑树的节点
- epoll_event：告诉内核需要监听什么事件，红黑树节点属性
  - EPOLL IN：对文件描述符可读
  - EPOLLOUT：对文件描述符可写
  - EPOLLPRI：对文件描述符有紧急数据需要可读（带外数据）
  - EPOLLERR：对应的文件描述符发生错误
  - EPOLLHUP：对应的文件描述符被挂断
  - EPOLLET：将 EPOLL 设置为「边缘触发 Edge Triggered」，这是相对「水平触发 Level Triggered」而言的。





##### 边缘触发 和 水平触发

最终会决定 epoll_wait 如何处理事件缓冲区的数据

- ET（边缘触发）：下次进入循环的时候，之前未处理的事件将会被丢弃，不会处理；
- LT（水平触发）：反之，水平触发会继续处理之前未处理的事件；

`epoll_wait`

- 功能：等待事件的产生，类似于 `select()` 调用；

```c++
// 等待 event 的到来
int epoll_wait(int epfd, struct epoll_event *events,
               int maxevents, int timeout);
```

- epfd：创建的文件描述符 fd；

- events：用来存放从「内核空间」得到的 event 集合；

  ```c++
  struct epoll_envent {
    	uint32_t			events;
    	epoll_data_t	data;	
  }
  ```

  

- maxevents：表示每次能处理的最大事件，告知内核这个 events 有多大，这个 `maxevents` 的值不能大于创建`epoll_create()` 时的 size；

- tiemout：超时时间（毫秒，0 会立即返回，-1 阻塞）

- 返回值：头文件

  ```c++
  #include <sys/epoll.h>
  ```

##### epoll 代码实现

```c
#include <sys/epoll.h>

int epfd, epct, i;
struct epoll_event event;
struct epoll_event events[20];

memset(events, 0, 20*sizeof(struct epoll_event));
epfd = epoll_create(1);			// 创建一个红黑树

event.data.fd = serverFd;			// 填充 fd
event.events = EPOLLIN;				//	填充 事件类型
epoll_ctl(epfd, EPOLL_CTL_ADD, serverFd.&event);	// 监听 serverFD


// 等待事件，开始处理

while(1){
  	epct = event_wait(epfd, event, 20, -1);		// 等待事件到来，阻塞模式，返回「就绪事件」，和 select() （全都返回）不一样
  
}


```



#### 1.2.4 时间复杂度比较

- select：O( n)
- poll: O(n)
- epoll: O(1)