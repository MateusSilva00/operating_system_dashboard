#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include <ctype.h>

#define MEMINFO_PATH "/proc/meminfo"
#define STAT_PATH "/proc/stat"
#define MAX_LINE_LENGTH 256
#define SECONDS_INTERVAL 2

#define PROC_PATH "/proc"
#define COMM_PATH_LEN 64
#define MAX_PROCESSES 1024

typedef struct
{
    long mem_total;
    long mem_free;
    long buffers;
    long cached;
    long swap_total;
    long swap_free;
    double mem_usage;
} MemInfo;

typedef struct
{
    unsigned long long total;
    unsigned long long idle;
} CpuInfo;

typedef struct {
    int pid;
    char name[COMM_PATH_LEN];
} ProcessInfo;

int get_meminfo(MemInfo *info)
{
    FILE *meminfoFile = fopen(MEMINFO_PATH, "r");
    if (meminfoFile == NULL)
    {
        perror("Erro ao abrir o arquivo /proc/meminfo");
        return -1;
    }

    char lineBuffer[MAX_LINE_LENGTH];

    info->mem_total = info->mem_free = -1;
    info->swap_total = info->swap_free = -1;
    info->buffers = info->cached = -1;

    while (fgets(lineBuffer, sizeof(lineBuffer), meminfoFile))
    {
        if (sscanf(lineBuffer, "MemTotal: %ld kB", &info->mem_total) == 1)
            continue;
        if (sscanf(lineBuffer, "MemFree: %ld kB", &info->mem_free) == 1)
            continue;
        if (sscanf(lineBuffer, "SwapTotal: %ld kB", &info->swap_total) == 1)
            continue;
        if (sscanf(lineBuffer, "SwapFree: %ld kB", &info->swap_free) == 1)
            continue;
        if (sscanf(lineBuffer, "Buffers: %ld kB", &info->buffers) == 1)
            continue;
        if (sscanf(lineBuffer, "Cached: %ld kB", &info->cached) == 1)
            continue;

        // if (info->mem_total != -1 && info->mem_free != -1 &&
        //     info->swap_total != -1 && info->swap_free != -1 &&
        //     info->buffers != 1 && info->cached != -1)
        // {
        //     break;
        // }
    }

    fclose(meminfoFile);

    if (info->mem_total == -1 && info->mem_free == -1 &&
        info->swap_total == -1 && info->swap_free == -1 &&
        info->buffers == -1 && info->cached == -1)
    {
        fprintf(stderr, "Erro ao encontrar todos os campos esperados em /proc/meminfo\n");
        return -1;
    }

    return 0;
}

int calc_mem_usage(MemInfo *info)
{
    long used_memory = info->mem_total - info->mem_free - info->buffers - info->cached;
    info->mem_usage = ((double)used_memory / info->mem_total) * 100;

    return 1;
}

void display_memory_info(MemInfo *info)
{   
    printf("\n========== 📊 MEMÓRIA DO SISTEMA ==========\n");
    printf("Memória Total : %ld kB\n", info->mem_total);
    printf("Memória Livre : %ld kB\n", info->mem_free);
    printf("Cached : %ld kb\n", info->cached);
    printf("Buffers : %ld kb\n", info->buffers);
    printf("Percentual utilizado : %.2f%%\n", info->mem_usage);
    printf("Swap Total    : %ld kB\n", info->swap_total);
    printf("Swap Livre    : %ld kB\n", info->swap_free);
    printf("===========================================\n");
}


int is_numeric(const char *str){
    for(; *str; str++){
        if (!isdigit(*str))
            return 0;
    }
    return 1;
}

int read_process_list(ProcessInfo *processes, int max_count) {
    DIR *proc_dir = opendir(PROC_PATH);

    if (!proc_dir) {
        perror("Failed to open /proc");
        return -1;
    }

    struct dirent *entry;
    int count = 0;

    while ((entry = readdir(proc_dir)) != NULL && count < max_count) {
        if (is_numeric(entry->d_name)) continue;

        int pid = atoi(entry->d_name);
        char comm_path[512];
        snprintf(comm_path, sizeof(comm_path), PROC_PATH"/%s/comm", entry->d_name);
            
        FILE *comm_file = fopen(comm_path,"r");
        if (!comm_file) continue;

        if (fgets(processes[count].name, COMM_PATH_LEN, comm_file)) {
            processes[count].name[strcspn(processes[count].name, "\n")] = '\0'; // remove newline
            processes[count].pid = pid;
            count++;
        }
        fclose(comm_file);
    }

    closedir(proc_dir);
    return count;
}

void display_process_list(ProcessInfo *processes, int count) {
    printf("\n============= 🧾 ACTIVE PROCESSES =============\n");
    printf("%-10s %-s\n", "PID", "Name");
    printf("----------------------------------------------\n");
    for (int i = 0; i < count; i++) {
        printf("%-10d %s\n", processes[i].pid, processes[i].name);
    }
    printf("==============================================\n");
}


int get_cpuinfo(CpuInfo *cpu)
{
    FILE *statFile = fopen(STAT_PATH, "r");
    if (!statFile)
    {
        perror("Erro ao abrir /proc/stat");
        return -1;
    }

    char linha[MAX_LINE_LENGTH];
    if (!fgets(linha, sizeof(linha), statFile))
    {
        fclose(statFile);
        return -1;
    }

    unsigned long long user, nice, system, idle, iowait, irq, softirq, steal;
    int readValuesCount = sscanf(linha, "cpu %llu %llu %llu %llu %llu %llu %llu %llu",
                       &user, &nice, &system, &idle, &iowait, &irq, &softirq, &steal);

    fclose(statFile);

    if (readValuesCount < 4)
        return -1;

    cpu->idle = idle + iowait;
    cpu->total = user + nice + system + idle + iowait + irq + softirq + steal;

    return 0;
}

void display_cpu_usage(double uso_percentual) {
    printf("🧠 Uso de CPU     : %.2f%%\n", uso_percentual);
}


int main(void)
{
    while (1) {
        system("clear");
        
        MemInfo meminfo;
        CpuInfo cpu1, cpu2;
        ProcessInfo processes[MAX_PROCESSES];

        if (get_meminfo(&meminfo) == 0){
            calc_mem_usage(&meminfo);
            display_memory_info(&meminfo);
        }

        if (get_cpuinfo(&cpu1) != 0) return 1;
        sleep(1);
        if (get_cpuinfo(&cpu2) != 0) return 1;

        // unsigned long long delta_total = cpu2.total - cpu1.total;
        // unsigned long long delta_idle = cpu2.idle - cpu1.idle;

        // double cpu_usage = 100.0 * (delta_total - delta_idle) / delta_total;


        // display_cpu_usage(cpu_usage);
        // int count = read_process_list(processes, MAX_PROCESSES);
        // if (count >= 0) {
        //     display_process_list(processes, count);
        // }

        // printf("\nAtualizando novamente em %d segundos...\n", SECONDS_INTERVAL);
        // sleep(SECONDS_INTERVAL);
    }

    return EXIT_SUCCESS;
}