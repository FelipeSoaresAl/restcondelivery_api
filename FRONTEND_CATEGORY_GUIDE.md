# Guia de Implementação Frontend: Gerenciamento de Categorias

Este documento descreve um fluxo de trabalho sugerido para a implementação da interface de usuário (UI) que consumirá os novos endpoints de categoria da API.

## 1. Endpoints da API a Serem Consumidos

O frontend precisará interagir com os seguintes endpoints:

*   **`POST /categories/store/{store_id}`**: Para criar uma nova categoria.
*   **`GET /categories/store/{store_id}`**: Para listar todas as categorias de uma loja.
*   **`POST /products/{product_id}/categories/{category_id}`**: Para associar uma categoria a um produto. (Endpoint a ser criado no backend).
*   **`DELETE /products/{product_id}/categories/{category_id}`**: Para desassociar uma categoria de um produto. (Endpoint a ser criado no backend).
*   **`PUT /categories/{category_id}`**: Para atualizar o nome de uma categoria. (Endpoint a ser criado no backend).
*   **`DELETE /categories/{category_id}`**: Para excluir uma categoria. (Endpoint a ser criado no backend).

## 2. Fluxo de UI/UX Sugerido

O fluxo pode ser dividido em duas áreas principais: gerenciamento de categorias e associação de categorias a produtos.

### Área 1: Painel de Gerenciamento de Categorias

Recomenda-se criar uma nova página ou um modal acessível a partir do painel principal do vendedor (dono da loja).

**Componentes e Lógica:**

1.  **Componente `CategoryManager` (Página ou Modal):**
    *   Ao carregar, faz uma chamada `GET /categories/store/{store_id}` para buscar e exibir a lista de categorias existentes.
    *   Deve conter um estado para armazenar a lista de categorias, estados de carregamento (`loading`) e de erro.

2.  **Componente `CategoryList`:**
    *   Renderiza a lista de categorias recebida do `CategoryManager`.
    *   Cada item da lista deve exibir o nome da categoria e ter botões para "Editar" e "Excluir".
        *   **Excluir**: Ao clicar, dispara uma chamada `DELETE /categories/{category_id}`. Após o sucesso, a lista de categorias deve ser atualizada (seja por uma nova chamada GET ou removendo o item do estado local).
        *   **Editar**: Ao clicar, pode transformar o texto do nome em um campo de input para edição e, ao salvar, disparar uma chamada `PUT /categories/{category_id}`.

3.  **Componente `CreateCategoryForm`:**
    *   Um formulário simples com um campo de texto para o nome da nova categoria e um botão "Adicionar".
    *   Ao submeter, faz uma chamada `POST /categories/store/{store_id}` com o nome da categoria.
    *   Após o sucesso, a lista de categorias no `CategoryManager` deve ser atualizada para exibir o novo item.

### Área 2: Associação de Categorias na Página do Produto

Na página de criação ou edição de um produto, o vendedor deve poder associar as categorias existentes.

**Componentes e Lógica:**

1.  **Componente `ProductForm` (Página de Edição/Criação de Produto):**
    *   Este componente provavelmente já existe.
    *   Ele deve ser modificado para incluir um novo componente, o `CategorySelector`.

2.  **Componente `CategorySelector`:**
    *   Ao carregar o formulário do produto, este componente deve fazer uma chamada `GET /categories/store/{store_id}` para buscar todas as categorias disponíveis para a loja.
    *   Ele deve renderizar essas categorias como uma lista de checkboxes, um campo de seleção múltipla (multi-select) ou um input de tags.
    *   Quando estiver editando um produto existente, as categorias já associadas a ele (que agora vêm na resposta da API do produto, `GET /products/{product_id}`) devem ser pré-selecionadas.

3.  **Lógica de Salvamento:**
    *   Quando o vendedor salva o formulário do produto, o frontend precisa comparar o estado inicial das categorias associadas com o novo estado.
    *   Para cada categoria que foi **marcada** (nova associação), deve ser feita uma chamada `POST /products/{product_id}/categories/{category_id}`.
    *   Para cada categoria que foi **desmarcada** (remoção da associação), deve ser feita uma chamada `DELETE /products/{product_id}/categories/{category_id}`.
    *   **Otimização**: O ideal é que o backend forneça um endpoint para salvar todas as associações de uma vez, enviando um array de `category_ids`. Se isso não for possível, as chamadas sequenciais são a alternativa.

## 3. Estrutura de Componentes (Exemplo Framework-Agnóstico)

```
/src
|-- /pages (ou /views)
|   |-- DashboardPage.js
|   |-- ProductEditPage.js
|   |-- ...
|-- /components
|   |-- /categories
|   |   |-- CategoryManager.js      # Componente principal da funcionalidade
|   |   |-- CategoryList.js         # Lista as categorias com botões de ação
|   |   |-- CreateCategoryForm.js   # Formulário de adição
|   |-- /products
|   |   |-- ProductForm.js          # Formulário principal do produto
|   |   |-- CategorySelector.js     # Seletor de categorias para o formulário
|-- /services (ou /api)
|   |-- categoryService.js        # Funções para chamadas à API de categorias
|   |-- productService.js         # Funções para chamadas à API de produtos
```

## Conclusão

Este fluxo garante que o gerenciamento de categorias seja centralizado e que a associação aos produtos seja intuitiva. A chave é garantir que o estado da UI seja sempre sincronizado com o backend, atualizando a lista de categorias após cada operação de criação, edição ou exclusão.
