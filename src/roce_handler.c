#include "roce_handler.h"
#include <rte_ether.h>
#include <rte_ip.h>
#include <rte_ethdev.h>
#include <rte_udp.h>
static int64_t _count=0;


/* pfc packet header within eth hdr */
int init_roce_handler(const char *ip_addr)
{
    last_timestamp=0;
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
    struct rte_mbuf *roce_response;
    struct rte_ether_hdr *response_eth_hdr;
    struct rte_ipv4_hdr *ipv4_hdr;
    struct rte_udp_hdr *udp_hdr;

    struct pfc_header *pfc_hdr;

    // 获取以太网头部  
    eth_hdr = rte_pktmbuf_mtod(pkt, struct rte_ether_hdr *);  
    
    // 获取ipv4头部  
    ipv4_hdr = rte_pktmbuf_mtod_offset(pkt, struct rte_ipv4_hdr *,   
                                      sizeof(struct rte_ether_hdr));  

#ifdef USE_DSCP_VALUE
    uint8_t dscp = (ipv4_hdr->type_of_service >> 2) & 0x3F;

    // 根据DSCP值获取优先级队列  
    uint8_t prio;  
    if (dscp <= 7) prio = 0;  
    else if (dscp <= 15) prio = 1;  
    else if (dscp <= 23) prio = 2;  
    else if (dscp <= 31) prio = 3;  
    else if (dscp <= 39) prio = 4;  
    else if (dscp <= 47) prio = 5;  
    else if (dscp <= 55) prio = 6;  
    else prio = 7;  
#endif

    // 跳过TCP包
    if (ipv4_hdr->next_proto_id==IPPROTO_TCP){
        return -1;
    }

    udp_hdr = rte_pktmbuf_mtod_offset(pkt, struct rte_udp_hdr *,
                                      sizeof(struct rte_ether_hdr) +
                                          sizeof(struct rte_ipv4_hdr));

    // 跳过非RoCE包
    if (rte_be_to_cpu_16(udp_hdr->src_port) != 4791) {  
        return -1;    // 是4791端口  
    }  
    const uint8_t *addr = eth_hdr->src_addr.addr_bytes;  

    // 将6字节MAC地址转换为uint64_t  
    uint64_t cur_timestamp = ((uint64_t)addr[0] << 40) |  
                    ((uint64_t)addr[1] << 32) |  
                    ((uint64_t)addr[2] << 24) |  
                    ((uint64_t)addr[3] << 16) |  
                    ((uint64_t)addr[4] << 8)  |  
                    ((uint64_t)addr[5]);  

    //printf("Before Test\n");
    if(cur_timestamp-last_timestamp<TIME_GAP || cur_timestamp-last_timestamp>FLOWLET_TIMEOUT){
        last_timestamp=cur_timestamp;
        return 0;
    }
    // printf("Pass the Test");
    uint16_t stop_time = 1+FLOWLET_TIMEOUT-(cur_timestamp-last_timestamp);
    last_timestamp=cur_timestamp;

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

    response_eth_hdr = rte_pktmbuf_mtod(roce_response, struct rte_ether_hdr *);  

    // 设置目标MAC地址为 01-80-C2-00-00-01  
    struct rte_ether_addr dst_mac;  
    //e8ebd358a02c
    // rte_ether_unformat_addr("01:80:c2:00:00:01", &dst_mac);  
    rte_ether_unformat_addr("e8:eb:d3:58:a0:2c", &dst_mac);  
    rte_ether_addr_copy(&dst_mac, &response_eth_hdr->dst_addr);  


    // 设置源MAC地址  
    rte_ether_addr_copy(&local_mac, &response_eth_hdr->src_addr);  
    response_eth_hdr->ether_type = htons(RTE_ETHER_TYPE_CTL);  

    // 构建PFC响应头部  
    pfc_hdr = (struct pfc_header *)(response_eth_hdr + 1);
    pfc_hdr->opcode = htons(0x0101);

#ifdef USE_DSCP_VALUE
    pfc_hdr->pev = htons(1<<prio)
#else
    pfc_hdr->pev = htons(0x00ff);
#endif

    for(int i=0;i<8;i++)
#ifdef USE_DSCP_VALUE
        if (i == prio) {  
            pfc_hdr->time[i] = htons((uint16_t)(stop_time/QUANTA_DURATION_NS));  
        } else {  
            pfc_hdr->time[i] = 0;  
        }  
#else
            pfc_hdr->time[i] = htons((uint16_t)(stop_time/QUANTA_DURATION_NS));  
#endif


    // pfc_hdr->time[0] = 1;
    for(int i=0;i<16;i++)
        pfc_hdr->pad[i] = (char) 0;

    // 发送响应  
    if(rte_eth_tx_burst(port_id, 0, &roce_response, 1) < 1) {  
        rte_pktmbuf_free(roce_response);  
        printf("RoCE Response Send Failed.\n");  
    }  
    rte_pktmbuf_free(pkt);  
    _count++;
    if(_count%100==0)
        printf("%ld PFC Send\n",_count);
    return 0;  
}
