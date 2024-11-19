#ifndef UDP_HANDLER_H
#define UDP_HANDLER_H

#include <rte_mbuf.h>

// UDP处理函数
int handle_udp_packet(struct rte_mbuf *pkt, uint16_t port_id);

// 初始化UDP处理器
int init_udp_handler(const char *ip_addr);

#endif /* UDP_HANDLER_H */