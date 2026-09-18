"""Ponto de entrada do Radar Concurso."""

from app.config.settings import APP_ENV, APP_TIMEZONE, NICHE_CONFIG_DIR
from app.services.niche_loader import NicheLoader


def main() -> None:
    loader = NicheLoader(NICHE_CONFIG_DIR)
    niches = loader.load_all()

    print("Radar Concurso")
    print(f"Ambiente: {APP_ENV}")
    print(f"Fuso horário: {APP_TIMEZONE}")
    print(f"Diretório de nichos: {NICHE_CONFIG_DIR}")
    print(f"Nichos carregados: {len(niches)}")

    for niche in niches:
        subnichos = niche.get("subnichos", [])
        ativos = sum(1 for item in subnichos if item.get("ativo", False))
        print(f"- {niche.get('nome', niche.get('id', 'Sem nome'))}: {ativos} subnichos ativos")


if __name__ == "__main__":
    main()
