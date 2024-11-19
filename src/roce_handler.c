#include "roce_handler.h"
#include <rte_ether.h>
#include <rte_ip.h>
#include <rte_ethdev.h>
#include <rte_udp.h>

static uint32_t local_ip;
static struct rte_ether_addr local_mac;

/* pfc packet header within eth hdr */
int init_roce_handler(const char *ip_addr)
{
    if (inet_pton(AF_INET, ip_addr, &local_ip) != 1) {  
        return -1;  
    }  

    // 获取本地MAC地址  
    rte_eth_macaddr_get(0, &local_mac);  
    return 0; 
}

int handle_roce_packet(struct rte_mempool *endsys_pktmbuf_pool, struct rte_mbuf *pkt, uint16_t port_id)
{
    struct rte_ether_hdr *eth_hdr;  
    struct roce_header *roce_hdr;  
    struct rte_mbuf *roce_response;
    struct rte_ether_hdr *response_eth_hdr;
    struct rte_ipv4_hdr *ipv4_hdr;
    struct rte_udp_hdr *udp_hdr;

    struct pfc_header *pfc_hdr;

    // 获取以太网头部  
    eth_hdr = rte_pktmbuf_mtod(pkt, struct rte_ether_hdr *);  
    
    // 获取RoCE头部  
    ipv4_hdr = rte_pktmbuf_mtod_offset(pkt, struct rte_ipv4_hdr *,   
                                      sizeof(struct rte_ether_hdr));  

    // 跳过TCP包
    if (ipv4_hdr->next_proto_id==IPPROTO_TCP){
        printf("It is a TCP\n");
        return -1;
    }

    udp_hdr = rte_pktmbuf_mtod_offset(pkt, struct rte_udp_hdr *,
                                      sizeof(struct rte_ether_hdr) +
                                          sizeof(struct rte_ipv4_hdr));

    // 跳过非RoCE包
    // if (rte_be_to_cpu_16(udp_hdr->dst_port) != 4791) {  
    //     return -1;    // 是4791端口  
    // }  
    printf("It is a RoCE\n");

    roce_hdr = rte_pktmbuf_mtod_offset(pkt, struct roce_header *,
                                       sizeof(struct rte_ether_hdr) +
                                           sizeof(struct rte_ipv4_hdr) +
                                           sizeof(struct rte_udp_hdr));


    // 分配新的mbuf用于RoCE响应  
    roce_response = rte_pktmbuf_alloc(endsys_pktmbuf_pool);  
    if (roce_response == NULL) {  
        rte_pktmbuf_free(pkt);  
        return -1;  
    }  

    // 计算总长度  
    uint16_t total_length = sizeof(struct rte_ether_hdr) + sizeof(struct pfc_header);  
    roce_response->data_len = total_length;  
    roce_response->pkt_len = total_length;  

    // 构建以太网头部  
    response_eth_hdr = rte_pktmbuf_mtod(roce_response, struct rte_ether_hdr *);  
    rte_ether_addr_copy(&eth_hdr->src_addr, &response_eth_hdr->dst_addr);  
    rte_ether_addr_copy(&local_mac, &response_eth_hdr->src_addr);  
    response_eth_hdr->ether_type = htons(RTE_ETHER_TYPE_CTL);  

    // 构建PFC响应头部  
    pfc_hdr = (struct pfc_header *)(response_eth_hdr + 1);
    pfc_hdr->opcode = htons(0x0101);
    pfc_hdr->pev = htons(0x00ff);
    for(int i=0;i<8;i++)
        pfc_hdr->time[i] = htons((uint16_t)(STOP_TIME/QUANTA_DURATION_NS));

    // pfc_hdr->time[0] = 1;
    for(int i=0;i<26;i++)
        pfc_hdr->pad[i] = (char) 0;

    // 发送响应  
    if(rte_eth_tx_burst(port_id, 0, &roce_response, 1) < 1) {  
        rte_pktmbuf_free(roce_response);  
        printf("RoCE Response Send Failed.\n");  
    }  
    printf("PFC send.");
    rte_pktmbuf_free(pkt);  

    return 0;  
}
