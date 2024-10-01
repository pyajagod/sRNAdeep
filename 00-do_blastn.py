import subprocess
import pandas as pd
import argparse
import os


def run_blastn(rna_file, db_name, output_file):
    cmd = [
        "blastn",
        "-query",
        rna_file,
        "-db",
        db_name,
        "-out",
        output_file,
        "-outfmt",
        "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore",
    ]
    subprocess.run(cmd, check=True)
    print(f"BLASTN results saved to {output_file}")


def parse_blast_results(output_file):
    columns = [
        "qseqid",
        "sseqid",
        "pident",
        "length",
        "mismatch",
        "gapopen",
        "qstart",
        "qend",
        "sstart",
        "send",
        "evalue",
        "bitscore",
    ]
    results = pd.read_csv(output_file, sep="\t", names=columns)
    return results


def do_blastn(rna_file, output_file, csv_output_file, db_name):

    # 运行BLASTN
    run_blastn(rna_file, db_name, output_file)

    # 解析BLAST结果
    results = parse_blast_results(output_file)

    # 保存结果到CSV文件
    results.to_csv(csv_output_file, index=False)
    print(f"Results saved to {csv_output_file}")


def main(args):
    # 创建BLAST数据库
    db_name = "human_protein_genes_db"
    subprocess.run(
        [
            "makeblastdb",
            "-in",
            "./train_input_seq.fasta",
            "-dbtype",
            "nucl",
            "-out",
            db_name,
        ],
        check=True,
    )

    os.makedirs("txtResults", exist_ok=True)
    os.makedirs("csvResults", exist_ok=True)
    for folder in args.fastafolder:
        for rna_file in os.listdir(folder):
            if not rna_file.endswith(".fasta") or rna_file.startswith("."):
                continue
            # rna_file = "rna_sequences.fasta"
            # db_name = "human_protein_genes_db"
            prexname = rna_file.split(".")[0]
            output_file = f"{prexname}.txt"
            csv_output_file = f"{prexname}.csv"

            do_blastn(
                os.path.join(folder, rna_file),
                os.path.join("txtResults", output_file),
                os.path.join("csvResults", csv_output_file),
                db_name,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "fastafolder",
        nargs="+",
        help="Input folder contains fasta files to be compare",
    )
    args = parser.parse_args()
    main(args)
    # main()
