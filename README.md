# Operating System Dashboard

Dashboard interativo para monitoramento de recursos do sistema operacional Linux.

## Funcionalidades
- Visualização em tempo real do uso de CPU, memória, processos e threads
- Listagem dos principais processos e suas threads
- Monitoramento de partições de disco e sistema de arquivos
- Navegação por diretórios e exibição de detalhes de arquivos
- Busca de arquivos por padrão de nome

## Estrutura do Projeto
- `main.py`: inicialização da aplicação
- `controller/`: lógica de controle e atualização dos dados
- `model/`: coleta de informações do sistema, processos e arquivos
- `view/`: interface gráfica (Tkinter + Matplotlib)

## Requisitos
- Python 3.11+
- Linux (utiliza /proc)
- Bibliotecas: tkinter, matplotlib

## Execução
```bash
python main.py
```

## Observações
- O dashboard utiliza apenas bibliotecas padrão do Python e matplotlib.
- Recomenda-se executar com permissões adequadas para acessar todos os dados do sistema.
