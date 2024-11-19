#ifndef ARP_HANDLER_H
#define ARP_HANDLER_H

#include <rte_mbuf.h>

// ARP处理函数
int handle_arp_packet(struct rte_mbuf *pkt, uint16_t port_id);

// 初始化ARP处理器
int init_arp_handler(const char *ip_addr);

#endif /* ARP_HANDLER_H */