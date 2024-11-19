#ifndef PROTOCOL_HANDLER_H
#define PROTOCOL_HANDLER_H

#include <rte_ether.h>
#include <rte_ip.h>
#include <rte_udp.h>

// 协议处理函数的类型定义
typedef int (*protocol_handler_fn)(struct rte_mbuf *pkt, uint16_t port_id);

// 协议处理器结构体
struct protocol_handler {
    uint16_t type;                  // 协议类型
    protocol_handler_fn handler;    // 处理函数
};

// 注册协议处理器
int register_protocol_handler(uint16_t type, protocol_handler_fn handler);

// 处理数据包
int process_packet(struct rte_mbuf *pkt, uint16_t port_id);

// 初始化协议处理系统
int init_protocol_handlers(void);

#endif /* PROTOCOL_HANDLER_H */