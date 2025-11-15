# Bookkeeper

## Introduction

This is a simple double-ledger bookkeeping tool for a small business, operated from the command line. 

## Installation

```shell
pip install pybookkeeper
```

## Usage

Create a directory for your ledger, and run `bookkeeper` from there. 
Your directory should contain `ledger-defs.txt`, which defines your ledger map, and the outline of the generated statements.

The transactions for accounts are stored in `data-YYYY-MM.txt` files.

For example, for year 2025, you would have:

- directory `2025`
- file `2025/ledger-defs.txt`
- files `2025/data-2025-01.txt`, `2025/data-2025-02.txt`, etc.

Running

```shell
bookkeeper 2025 
```

will generate in directory `output/`, which is created if it does not exist, 
the files `general-ledger.txt`, `statement.txt` and `journal.txt`.

You can change the output directory with `--output-directory`, as follows

```shell
bookkeeper 2025 --output-directory 2025-books
```

## Release process

- [ ] Update version in `pyproject.toml`
- [ ] Update ChangeLog
- [ ] Run tests with `tox`
- [ ] Tag release
