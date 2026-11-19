# Lab 03: multiplication without a multiplier. Fill in the TODO (see README.md).

    .text

    .global mul_hw
    .type   mul_hw, @function
# unsigned mul_hw(unsigned a, unsigned b): the hardware's way, one instruction (the M extension). Given.
mul_hw:
    mul     a0, a0, a1
    ret

    .global mul_soft
    .type   mul_soft, @function
# unsigned mul_soft(unsigned a, unsigned b): a * b (the low 32 bits), with RV32I only:
# no mul, no div. Long multiplication in binary, like on paper: for each bit of b that is 1,
# add a copy of a shifted left by that bit's position.
mul_soft:
    # TODO
    li      a0, 0
    ret
