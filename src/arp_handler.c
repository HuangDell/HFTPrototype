#include <rte_ether.h>
#include <rte_arp.h>
#include <rte_ethdev.h>
#include "arp_handler.h"

static uint32_t local_ip;
static struct rte_ether_addr local_mac;

int init_arp_handler(const char *ip_addr) {
    // 转换IP地址字符串为网络字节序的32位整数
    if (inet_pton(AF_INET, ip_addr, &local_ip) != 1) {
        return -1;
    }

    // 获取本地MAC地址
    rte_eth_macaddr_get(0, &local_mac);
    return 0;
}

int handle_arp_packet(struct rte_mempool *endsys_pktmbuf_pool,struct rte_mbuf *pkt, uint16_t port_id) {
    struct rte_ether_hdr *eth_hdr;
    struct rte_arp_hdr *arp_hdr;
    struct rte_mbuf *arp_reply;
    struct rte_ether_hdr *reply_eth_hdr;
    struct rte_arp_hdr *reply_arp_hdr;

    eth_hdr = rte_pktmbuf_mtod(pkt, struct rte_ether_hdr *);
    arp_hdr = rte_pktmbuf_mtod_offset(pkt, struct rte_arp_hdr *, 
                                     sizeof(struct rte_ether_hdr));

    // 只处理ARP请求
    if (rte_be_to_cpu_16(arp_hdr->arp_opcode) != RTE_ARP_OP_REQUEST) {
        rte_pktmbuf_free(pkt);
        return 0;
    }

    // 检查目标IP是否匹配
    if (arp_hdr->arp_data.arp_tip != local_ip) {
        rte_pktmbuf_free(pkt);
        return 0;
    }

    // 分配新的mbuf用于ARP响应
    arp_reply = rte_pktmbuf_alloc(endsys_pktmbuf_pool);
    if (arp_reply == NULL) {
        rte_pktmbuf_free(pkt);
        return -1;
    }
    // 计算总长度
    uint16_t total_length = sizeof(struct rte_ether_hdr) + sizeof(struct rte_arp_hdr);
    arp_reply->data_len = total_length;
    arp_reply -> pkt_len = total_length; 

    // 构建以太网头
    reply_eth_hdr = rte_pktmbuf_mtod(arp_reply, struct rte_ether_hdr *);
    rte_ether_addr_copy(&eth_hdr->src_addr, &reply_eth_hdr->dst_addr);
    rte_ether_addr_copy(&local_mac, &reply_eth_hdr->src_addr);
    reply_eth_hdr->ether_type = htons(RTE_ETHER_TYPE_ARP);

    // 构建ARP响应
    reply_arp_hdr = (struct rte_arp_hdr *)(reply_eth_hdr + 1);
    reply_arp_hdr->arp_hardware = htons(RTE_ARP_HRD_ETHER);
    reply_arp_hdr->arp_protocol = htons(RTE_ETHER_TYPE_IPV4);
    reply_arp_hdr->arp_hlen = RTE_ETHER_ADDR_LEN;
    reply_arp_hdr->arp_plen = sizeof(uint32_t);
    reply_arp_hdr->arp_opcode = htons(RTE_ARP_OP_REPLY);

    // 设置ARP数据
    rte_ether_addr_copy(&local_mac, &reply_arp_hdr->arp_data.arp_sha);
    reply_arp_hdr->arp_data.arp_sip = local_ip;
    rte_ether_addr_copy(&arp_hdr->arp_data.arp_sha, 
                        &reply_arp_hdr->arp_data.arp_tha);
    reply_arp_hdr->arp_data.arp_tip = arp_hdr->arp_data.arp_sip;

    // 发送响应
    if(rte_eth_tx_burst(port_id, 0, &arp_reply, 1) < 1) {  
        rte_pktmbuf_free(arp_reply);  
        printf("ARP Reply Send Failed.");
    }  
    rte_pktmbuf_free(pkt);
    
    return 0;
}