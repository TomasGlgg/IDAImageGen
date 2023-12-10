from PIL import Image
from sys import argv
import random

if len(argv) != 3:
    print('Usage:\n\tpython {0} IMAGE LxW\nExample:\n\tpython {0} example.png 100x100'.format(argv[0]))
    exit()

MAX = 10

class CodeGenerator:
    regs = 'eax', 'ebx', 'ecx', 'edx'
    random_reg = lambda: random.choice(CodeGenerator.regs)

    opcodes_one_reg = 'inc', 'dec'
    opcodes_reg_int4 = 'shr', 'shl'  # 4 bits (1-16)
    opcodes_reg_int32 = 'or', 'add', 'mov', 'cmp'  # 32 bits (4 bytes)
    opcodes_two_reg = 'add', 'xor', 'or', 'test', 'cmp', 'add'

    random_num = lambda bits: hex(random.randint(1, 2**bits))

    @staticmethod
    def gen_effective_address():
        variants = (
            lambda: f'[{CodeGenerator.random_reg()} + {CodeGenerator.random_num(4)}]',  # [eNx + M]
            lambda: f'[{CodeGenerator.random_reg()} + {CodeGenerator.random_reg()}]',  # [eNx + eMx]
            lambda: f'[{CodeGenerator.random_reg()} + {CodeGenerator.random_reg()}*2]'  # [eNx + eMx*K]
            )
        return random.choice(variants)()

    @staticmethod
    def random_opcode():
        variants = (
            lambda: f'{random.choice(CodeGenerator.opcodes_one_reg)} {CodeGenerator.random_reg()}',
            lambda: f'{random.choice(CodeGenerator.opcodes_reg_int4)} {CodeGenerator.random_reg()}, {CodeGenerator.random_num(4)}',
            lambda: f'{random.choice(CodeGenerator.opcodes_reg_int32)} {CodeGenerator.random_reg()}, {CodeGenerator.random_num(32)}',
            lambda: f'{random.choice(CodeGenerator.opcodes_two_reg)} {CodeGenerator.random_reg()}, {CodeGenerator.random_reg()}',
            lambda: f'lea {CodeGenerator.random_reg()}, {CodeGenerator.gen_effective_address()}'
        )
        return random.choice(variants)()

    @staticmethod
    def generate_block(count):
        return '\n\t'.join(CodeGenerator.random_opcode() for _ in range(count))


def generate_node(count, node_name, next_node_name):
    code = f'{node_name}:\n'
    code += '\tvfmaddsub132ps xmm0, xmm1, [edi + esi*4 + 0x8000164]\n\t'  # wide opcode for static node width in graph
    code += CodeGenerator.generate_block(count)
    code += f'\n\tjmp {next_node_name}\n\n'
    return code

def generate_switch_table(count):
    code = 's:\n'
    code += '\n'.join(f'\tdd node_{x}_0' for x in range(count))
    code += '\n\n'
    return code

def get_pixel(image, x, y):
    pixel = image.getpixel((x, y))
    return round(pixel/256*MAX)

def generate_graph(file, image):
    x, y = image.size
    file.write('global _start\n\nsection .data\n')
    file.write(generate_switch_table(x))
    file.write('section .text\n_start:\n')
    file.write('jmp [s + eax*4]\n\n')  # switch
    for i in range(x):
        for j in range(y):
            current_node = f'node_{i}_{j}'
            next_node = 'done' if j == y-1 else f'node_{i}_{j+1}'
            if i == 0: count = MAX
            else: count = get_pixel(image, i, j)
            file.write(generate_node(count, current_node, next_node))
    file.write('done: ret\n\n')

size = tuple(map(int, argv[2].split('x')))
image = Image.open(argv[1]).convert('L').resize(size)
with open('code.asm', 'w') as file:
    generate_graph(file, image)
