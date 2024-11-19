#ifndef ROCE_HANDLER_H
#define ROCE_HANDLER_H
#include <rte_mbuf.h>

#define RTE_ETHER_TYPE_ROCE 0x8915 
#define RTE_ETHER_TYPE_CTL 0x8808
// 100Gbps 的quanta大小为5.12ns
#define QUANTA_DURATION_NS 5.12
// 单位 ns
#define STOP_TIME 1000

struct pfc_header
{
    uint16_t opcode;
    uint16_t pev; /* priority enable vector */
    uint16_t time[8];
    char pad[26];
} __attribute__((__packed__));

struct roce_header {  
    uint8_t opcode;        // 操作码  
    uint8_t flags;         // 标志位  
    uint16_t partition_key;
    // uint8_t reserved;
    uint32_t qp_num;       // QP号  
    uint8_t ack_request;
    uint32_t psn;         // 包序列号  
} __attribute__((__packed__));  

// roce处理函数
int handle_roce_packet(struct rte_mempool *endsys_pktmbuf_pool,struct rte_mbuf *pkt, uint16_t port_id);

// 初始化UDP处理器
int init_roce_handler(const char *ip_addr);

#endif /* ROCE_HANDLER_H */