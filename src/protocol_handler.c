#include <rte_common.h>
#include <rte_mbuf.h>
#include <rte_ether.h>
#include "protocol_handler.h"

#define MAX_HANDLERS 32

static struct protocol_handler handlers[MAX_HANDLERS];
static int num_handlers = 0;

int register_protocol_handler(uint16_t type, protocol_handler_fn handler) {
    if (num_handlers >= MAX_HANDLERS) {
        return -1;
    }

    handlers[num_handlers].type = type;
    handlers[num_handlers].handler = handler;
    num_handlers++;

    return 0;
}

int process_packet(struct rte_mbuf *pkt, uint16_t port_id) {
    struct rte_ether_hdr *eth_hdr;
    int i;

    eth_hdr = rte_pktmbuf_mtod(pkt, struct rte_ether_hdr *);
    
    // 遍历所有注册的处理器
    for (i = 0; i < num_handlers; i++) {
        if (handlers[i].type == rte_be_to_cpu_16(eth_hdr->ether_type)) {
            return handlers[i].handler(pkt, port_id);
        }
    }

    // 未找到对应的处理器，释放数据包
    rte_pktmbuf_free(pkt);
    return 0;
}

int init_protocol_handlers(void) {
    num_handlers = 0;
    return 0;
}