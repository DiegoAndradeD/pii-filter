import json
import os

INPUT_FILENAME = "dataset.json"
OUTPUT_FILENAME = "corrected_dataset.json"


def correct_all_spans():
    """
    Reads a dataset, recalculates all ground_truth spans based on the prompt_text,
    and writes a new, corrected dataset file.
    """
    if not os.path.exists(INPUT_FILENAME):
        print(f"Erro: Arquivo de entrada '{INPUT_FILENAME}' não encontrado.")
        return

    with open(INPUT_FILENAME, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # Garante que o dataset seja sempre uma lista
    if not isinstance(dataset, list):
        dataset = [dataset]

    corrected_dataset = []
    print(f"Processando {len(dataset)} caso(s) de teste...")

    for i, test_case in enumerate(dataset):
        prompt_text = test_case.get("prompt_text", "")
        ground_truth = test_case.get("ground_truth", [])

        if not prompt_text or not ground_truth:
            corrected_dataset.append(test_case)
            continue

        new_ground_truth = []
        last_found_index = 0

        for pii_entry in ground_truth:
            value = pii_entry.get("value")
            if not value:
                new_ground_truth.append(pii_entry)
                continue

            # Procura pelo valor a partir da última posição encontrada para lidar com duplicatas
            try:
                start_index = prompt_text.find(value, last_found_index)
                if start_index == -1:
                    print(
                        f"  Aviso no caso #{i+1}: Valor '{value[:30]}...' não encontrado no texto. Mantendo span original."
                    )
                    new_span = pii_entry.get("span", [0, 0])
                else:
                    end_index = start_index + len(value)
                    new_span = [start_index, end_index]
                    # Atualiza a posição para a próxima busca
                    last_found_index = end_index

                # Cria a nova entrada com o span corrigido
                new_entry = pii_entry.copy()
                new_entry["span"] = new_span
                new_ground_truth.append(new_entry)

            except Exception as e:
                print(f"  Erro ao processar o valor '{value}': {e}")
                new_ground_truth.append(pii_entry)  # Mantém o original em caso de erro

        # Atualiza o caso de teste com o ground_truth corrigido
        corrected_case = test_case.copy()
        corrected_case["ground_truth"] = new_ground_truth
        corrected_dataset.append(corrected_case)
        print(
            f"  Caso #{i+1} ('{test_case.get('metadata', {}).get('id')}'): Spans recalculados."
        )

    # Salva o novo dataset em um arquivo de saída
    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        json.dump(corrected_dataset, f, ensure_ascii=False, indent=2)

    print(f"\nSucesso! Dataset corrigido salvo em '{OUTPUT_FILENAME}'.")


if __name__ == "__main__":
    correct_all_spans()
