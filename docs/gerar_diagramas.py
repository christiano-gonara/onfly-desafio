"""Gera os diagramas automáticos de docs/DIAGRAMAS.md.

Reescreve só o que está entre os marcadores <!-- AUTO:nome:inicio --> e
<!-- AUTO:nome:fim -->. Usa apenas a biblioteca padrão do Python.

Uso:
    python3 docs/gerar_diagramas.py            # atualiza o arquivo
    python3 docs/gerar_diagramas.py --check    # só confere; sai com código 1 se estiver desatualizado
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PACOTE = "onfly_report"
CODIGO = RAIZ / "src" / PACOTE
DESTINO = RAIZ / "docs" / "DIAGRAMAS.md"

# Só usado quando o git não está disponível para listar os arquivos.
IGNORAR = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".DS_Store"}

# Descrições escritas à mão, só para pastas (arquivos .py usam a docstring).
DESCRICAO_DE_PASTA = {
    ".github": "Verificação automática (CI)",
    "data": "Arquivos CSV de entrada",
    "docs": "Diagramas e mapa mental",
    "entrega": "Documentos da entrega",
    "output": "Onde o relatório é gerado",
    "src": "Código do CLI",
    "src/onfly_report/repositories": "Leitura dos CSV",
    "src/onfly_report/services": "Regras de negócio",
    "tests": "Testes",
}


def primeira_linha(texto: str | None) -> str:
    if not texto:
        return ""
    linhas = texto.strip().splitlines()
    return linhas[0].strip().rstrip(".") if linhas else ""


def ler_arvore(caminho: Path) -> ast.Module:
    return ast.parse(caminho.read_text(encoding="utf-8"))


def modulos() -> dict[str, Path]:
    """Mapa 'onfly_report.services.row_parser' -> caminho do arquivo, sem os __init__ vazios."""
    achados: dict[str, Path] = {}
    for caminho in sorted(CODIGO.rglob("*.py")):
        arvore = ler_arvore(caminho)
        if caminho.name == "__init__.py":
            tipos = (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef)
            if not any(isinstance(no, tipos) for no in arvore.body):
                continue
        partes = list(caminho.relative_to(CODIGO.parent).with_suffix("").parts)
        if partes[-1] == "__init__":
            partes.pop()
        achados[".".join(partes)] = caminho
    return achados


def dependencias(achados: dict[str, Path]) -> list[tuple[str, str]]:
    """Pares (quem usa, quem é usado), só entre módulos do próprio projeto."""
    ligacoes: set[tuple[str, str]] = set()
    for nome, caminho in achados.items():
        partes = nome.split(".")
        pacote = partes if caminho.name == "__init__.py" else partes[:-1]
        for no in ast.walk(ler_arvore(caminho)):
            alvos: list[list[str]] = []
            if isinstance(no, ast.ImportFrom):
                if no.level:
                    base = pacote[: len(pacote) - (no.level - 1)]
                else:
                    base = []
                alvo = base + (no.module.split(".") if no.module else [])
                alvos.append(alvo)
                alvos.extend(alvo + [item.name] for item in no.names)
            elif isinstance(no, ast.Import):
                alvos.extend(item.name.split(".") for item in no.names)
            for alvo in alvos:
                destino = ".".join(alvo)
                if destino in achados and destino != nome:
                    ligacoes.add((nome, destino))
    return sorted(ligacoes)


def id_mermaid(nome: str) -> str:
    return re.sub(r"\W", "_", nome)


def grafo(achados: dict[str, Path], ligacoes: list[tuple[str, str]]) -> str:
    grupos: dict[str, list[str]] = {}
    for nome, caminho in achados.items():
        pasta = "/".join(nome.split(".")[:-1]) + "/"
        grupos.setdefault(pasta, []).append(nome)

    usados_por: dict[str, int] = {}
    for _, destino in ligacoes:
        usados_por[destino] = usados_por.get(destino, 0) + 1
    compartilhados = sorted(nome for nome, vezes in usados_por.items() if vezes >= 3)

    linhas = ["```mermaid", "flowchart LR"]
    for pasta in sorted(grupos):
        linhas.append(f'    subgraph g_{id_mermaid(pasta)}["{pasta}"]')
        for nome in sorted(grupos[pasta]):
            linhas.append(f'        {id_mermaid(nome)}["{achados[nome].name}"]')
        linhas.append("    end")
    for origem, destino in ligacoes:
        linhas.append(f"    {id_mermaid(origem)} --> {id_mermaid(destino)}")
    if compartilhados:
        linhas.append("    classDef compartilhado fill:#e8f0fe,stroke:#4a6fa5,color:#1f3a5f")
        linhas.append(f"    class {','.join(id_mermaid(n) for n in compartilhados)} compartilhado")
    linhas.append("```")
    return "\n".join(linhas)


def listar_arquivos() -> list[str]:
    try:
        saida = subprocess.run(
            ["git", "-c", "core.quotepath=off", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        caminhos = [linha for linha in saida.splitlines() if linha]
    except (OSError, subprocess.CalledProcessError):
        caminhos = [
            p.relative_to(RAIZ).as_posix()
            for p in RAIZ.rglob("*")
            if p.is_file() and not IGNORAR & set(p.relative_to(RAIZ).parts)
        ]
    return sorted(c for c in caminhos if (RAIZ / c).is_file())


def descricao_de_arquivo(caminho: Path) -> str:
    completo = RAIZ / caminho
    if caminho.suffix != ".py" or not completo.is_file():
        return ""
    try:
        return primeira_linha(ast.get_docstring(ler_arvore(completo)))
    except SyntaxError:
        return ""


def linhas_da_arvore(no: dict, prefixo: str = "", pasta: Path = Path()):
    itens = sorted(
        ((nome, filho) for nome, filho in no.items() if nome != ".gitkeep"),
        key=lambda item: (item[1] is None, item[0].lower()),
    )
    for posicao, (nome, filho) in enumerate(itens):
        ultimo = posicao == len(itens) - 1
        caminho = pasta / nome
        esquerda = prefixo + ("└── " if ultimo else "├── ") + nome + ("/" if filho is not None else "")
        if filho is None:
            descricao = descricao_de_arquivo(caminho)
        else:
            descricao = DESCRICAO_DE_PASTA.get(caminho.as_posix(), "")
        yield esquerda, descricao
        if filho is not None:
            yield from linhas_da_arvore(filho, prefixo + ("    " if ultimo else "│   "), caminho)


def arvore() -> str:
    raiz: dict = {}
    for caminho in listar_arquivos():
        no = raiz
        partes = Path(caminho).parts
        for parte in partes[:-1]:
            no = no.setdefault(parte, {})
        no[partes[-1]] = None

    itens = [(f"{RAIZ.name}/", "")] + list(linhas_da_arvore(raiz))
    largura = max(len(esquerda) for esquerda, _ in itens)
    linhas = [f"{esquerda.ljust(largura)}  # {descricao}" if descricao else esquerda for esquerda, descricao in itens]
    return "```text\n" + "\n".join(linhas) + "\n```"


def tabela_de_funcoes(achados: dict[str, Path]) -> str:
    def celula(texto: str) -> str:
        return texto.replace("|", "\\|") or "—"

    linhas = ["| Arquivo | O que define | Resumo |", "|-|-|-|"]
    for caminho in sorted(achados.values()):
        arquivo = caminho.relative_to(CODIGO).as_posix()
        for no in ler_arvore(caminho).body:
            if isinstance(no, ast.ClassDef):
                linhas.append(f"| `{arquivo}` | `{no.name}` (classe) | {celula(primeira_linha(ast.get_docstring(no)))} |")
                for item in no.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_"):
                        resumo = celula(primeira_linha(ast.get_docstring(item)))
                        linhas.append(f"| `{arquivo}` | `{no.name}.{item.name}()` | {resumo} |")
            elif isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                linhas.append(f"| `{arquivo}` | `{no.name}()` | {celula(primeira_linha(ast.get_docstring(no)))} |")
    return "\n".join(linhas)


def substituir(texto: str, nome: str, conteudo: str) -> str:
    padrao = re.compile(rf"(<!-- AUTO:{nome}:inicio -->\n).*?(\n<!-- AUTO:{nome}:fim -->)", re.DOTALL)
    if not padrao.search(texto):
        raise SystemExit(f"Não achei os marcadores AUTO:{nome} em {DESTINO.relative_to(RAIZ)}")
    return padrao.sub(lambda m: m.group(1) + conteudo + m.group(2), texto)


def main() -> int:
    parser = argparse.ArgumentParser(description="Atualiza os diagramas automáticos de docs/DIAGRAMAS.md")
    parser.add_argument("--check", action="store_true", help="só confere; sai com código 1 se estiver desatualizado")
    args = parser.parse_args()

    achados = modulos()
    atual = DESTINO.read_text(encoding="utf-8")
    novo = substituir(atual, "grafo", grafo(achados, dependencias(achados)))
    novo = substituir(novo, "arvore", arvore())
    novo = substituir(novo, "funcoes", tabela_de_funcoes(achados))

    if novo == atual:
        print("docs/DIAGRAMAS.md já está em dia.")
        return 0
    if args.check:
        print("docs/DIAGRAMAS.md está desatualizado. Rode: python3 docs/gerar_diagramas.py")
        return 1
    DESTINO.write_text(novo, encoding="utf-8")
    print("docs/DIAGRAMAS.md atualizado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
