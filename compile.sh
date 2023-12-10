nasm -f elf32 code.asm -o out.o && ld -m elf_i386 -s -o out.elf out.o
