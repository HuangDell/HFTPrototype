#include <rte_ether.h>
#include <rte_ip.h>
#include <rte_ethdev.h>
#include <rte_udp.h>
#include "udp_handler.h"

static uint32_t local_ip;
static struct rte_ether_addr local_mac;

int init_udp_handler(const char *ip_addr) {
    // 转换IP地址字符串为网络字节序的32位整数
    if (inet_pton(AF_INET, ip_addr, &local_ip) != 1) {
        return -1;
    }

    // 获取本地MAC地址
    rte_eth_macaddr_get(0, &local_mac);
    return 0;
}

int handle_udp_packet(struct rte_mempool *endsys_pktmbuf_pool,struct rte_mbuf *pkt, uint16_t port_id) {
    struct rte_ether_hdr *eth_hdr;
    struct rte_ipv4_hdr *ip_hdr;
    struct rte_udp_hdr *udp_hdr;
    struct rte_mbuf *udp_reply;
    struct rte_ether_hdr *reply_eth_hdr;
    struct rte_ipv4_hdr *reply_ip_hdr;
    struct rte_udp_hdr *reply_udp_hdr;

    eth_hdr = rte_pktmbuf_mtod(pkt, struct rte_ether_hdr *);
    ip_hdr = rte_pktmbuf_mtod_offset(pkt, struct rte_ipv4_hdr *, 
                                    sizeof(struct rte_ether_hdr));
    udp_hdr = rte_pktmbuf_mtod_offset(pkt, struct rte_udp_hdr *,
                                     sizeof(struct rte_ether_hdr) + 
                                     sizeof(struct rte_ipv4_hdr));

    // 检查目标IP是否匹配
    if (ip_hdr->dst_addr != local_ip) {
        rte_pktmbuf_free(pkt);
        return 0;
    }

    // 分配新的mbuf用于UDP响应
    udp_reply = rte_pktmbuf_alloc(endsys_pktmbuf_pool);
    if (udp_reply == NULL) {
        rte_pktmbuf_free(pkt);
        return -1;
    }
    // 计算总长度
    uint16_t total_length = sizeof(struct rte_ether_hdr) + sizeof(struct rte_ipv4_hdr) + sizeof(struct rte_udp_hdr);
    udp_reply->data_len = total_length;
    udp_reply->pkt_len = total_length;

    // 构建以太网头
    reply_eth_hdr = rte_pktmbuf_mtod(udp_reply, struct rte_ether_hdr *);
    rte_ether_addr_copy(&eth_hdr->src_addr, &reply_eth_hdr->dst_addr);
    rte_ether_addr_copy(&local_mac, &reply_eth_hdr->src_addr);
    reply_eth_hdr->ether_type = htons(RTE_ETHER_TYPE_IPV4);

    // 构建IP头
    reply_ip_hdr = (struct rte_ipv4_hdr *)(reply_eth_hdr + 1);
    reply_ip_hdr->version_ihl = 0x45;
    reply_ip_hdr->type_of_service = 0;
    reply_ip_hdr->total_length = htons(sizeof(struct rte_ipv4_hdr) + 
                                      sizeof(struct rte_udp_hdr));
    reply_ip_hdr->packet_id = 0;
    reply_ip_hdr->fragment_offset = 0;
    reply_ip_hdr->time_to_live = 64;
    reply_ip_hdr->next_proto_id = IPPROTO_UDP;
    reply_ip_hdr->src_addr = local_ip;
    reply_ip_hdr->dst_addr = ip_hdr->src_addr;
    reply_ip_hdr->hdr_checksum = 0;
    reply_ip_hdr->hdr_checksum = rte_ipv4_cksum(reply_ip_hdr);

    // 构建UDP头
    reply_udp_hdr = (struct rte_udp_hdr *)(reply_ip_hdr + 1);
    reply_udp_hdr->src_port = udp_hdr->dst_port;
    reply_udp_hdr->dst_port = udp_hdr->src_port;
    reply_udp_hdr->dgram_len = htons(sizeof(struct rte_udp_hdr));
    reply_udp_hdr->dgram_cksum = 0;
    reply_udp_hdr->dgram_cksum = rte_ipv4_udptcp_cksum(reply_ip_hdr, reply_udp_hdr);

    // 发送响应
    rte_eth_tx_burst(port_id, 0, &udp_reply, 1);
    rte_pktmbuf_free(pkt);

    return 0;
}