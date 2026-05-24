-- =============================================
-- PoupeJá — Base de dados no Supabase
-- Cola este SQL no Supabase > SQL Editor > Run
-- =============================================

-- Tabela de produtos (catálogo)
create table if not exists produtos (
  id          text primary key,
  nome        text not null,
  emoji       text,
  categoria   text,
  ativo       boolean default true,
  criado_em   timestamptz default now()
);

-- Tabela de preços (histórico diário)
create table if not exists precos (
  id            bigserial primary key,
  produto_id    text references produtos(id),
  supermercado  text not null,      -- 'continente', 'pingodoce', 'lidl'
  preco         numeric(8,2) not null,
  nome_real     text,               -- nome exato no supermercado
  imagem        text,
  url           text,
  em_promocao   boolean default false,
  data          date not null,
  atualizado_em timestamptz default now(),
  unique (produto_id, supermercado, data)
);

-- Tabela de configuração
create table if not exists config (
  chave text primary key,
  valor text
);

-- Índices para pesquisa rápida
create index if not exists idx_precos_produto on precos(produto_id);
create index if not exists idx_precos_data on precos(data);
create index if not exists idx_precos_super on precos(supermercado);

-- Permitir leitura pública (o website lê sem autenticação)
alter table produtos enable row level security;
alter table precos   enable row level security;
alter table config   enable row level security;

create policy "Leitura pública de produtos"
  on produtos for select using (true);

create policy "Leitura pública de preços"
  on precos for select using (true);

create policy "Leitura pública de config"
  on config for select using (true);

-- Inserir catálogo de produtos
insert into produtos (id, nome, emoji, categoria) values
  ('leite-mimosa-1l',        'Leite Mimosa 1L',         '🥛', 'lacticinios'),
  ('pao-de-forma',           'Pão de forma',            '🍞', 'padaria'),
  ('ovos-m-12',              'Ovos M (12 un.)',          '🥚', 'frescos'),
  ('frango-inteiro',         'Frango inteiro',           '🍗', 'carnes'),
  ('queijo-flamengo',        'Queijo flamengo',          '🧀', 'lacticinios'),
  ('azeite-1l',              'Azeite virgem 1L',         '🫒', 'mercearia'),
  ('arroz-agulha-1kg',       'Arroz agulha 1kg',         '🍚', 'mercearia'),
  ('detergente-loica-500ml', 'Detergente loiça 500ml',   '🧴', 'limpeza'),
  ('tomate-kg',              'Tomate (kg)',               '🍅', 'frutas-legumes'),
  ('banana-kg',              'Banana (kg)',               '🍌', 'frutas-legumes'),
  ('iogurte-natural-pack4',  'Iogurte natural (pack 4)', '🥛', 'lacticinios'),
  ('agua-5l',                'Água 5L',                  '💧', 'bebidas'),
  ('manteiga-250g',          'Manteiga 250g',             '🧈', 'lacticinios'),
  ('cafe-delta-250g',        'Café Delta 250g',           '☕', 'mercearia'),
  ('massa-esparguete-500g',  'Massa esparguete 500g',    '🍝', 'mercearia')
on conflict (id) do nothing;

-- View útil: preço de hoje por produto e supermercado
create or replace view precos_hoje as
select
  p.id          as produto_id,
  p.nome,
  p.emoji,
  p.categoria,
  pr.supermercado,
  pr.preco,
  pr.em_promocao,
  pr.nome_real,
  pr.imagem,
  pr.url
from produtos p
left join precos pr on pr.produto_id = p.id and pr.data = current_date
where p.ativo = true;

-- View útil: melhor preço de hoje por produto
create or replace view melhor_preco_hoje as
select
  produto_id,
  supermercado as mais_barato_em,
  preco        as melhor_preco
from precos
where data = current_date
  and preco = (
    select min(preco)
    from precos p2
    where p2.produto_id = precos.produto_id
      and p2.data = current_date
  );
