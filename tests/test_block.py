from bookkeeper.ledger import Block, Account, Entry
from decimal import Decimal


def create_account(balance):
    acc = Account("1000", "Velkatili")
    acc.add_entry(Entry("1000", Decimal(balance)))
    return acc


def test_account():
    acc = Account("1000", "Velkatili")
    assert acc.balance == 0

    acc.add_entry(Entry("1000", Decimal("3.50")))

    assert acc.balance == Decimal((0, (3,5), -1))

    acc = create_account("100")
    assert acc.balance == Decimal((0, (1, 0, 0), 0))

    assert acc.sum() == acc.balance, \
        "Account should provide conveniency sum()"


def test_blocks():
    block = Block()
    assert block.sum() == 0, "Empty block should report zero sum"

    acc = create_account("6.7")
    block = Block([acc])

    assert block.sum() == Decimal("6.7")

    block = Block([Block()])

    assert block.sum() == Decimal(), "Nested blocks should be ok"

    block = Block([Block([acc])])

    assert block.sum() == Decimal("6.7"), "Nested blocks should be ok"

    acc2 = create_account("3.3")
    block2 = Block([acc2, block])

    assert block2.sum() == Decimal("10")
