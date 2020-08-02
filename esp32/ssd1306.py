import fonts
from micropython import const

# Made from https://github.com/4ilo/ssd1306-stm32HAL
# TODO: Get it to work, still no success :(

class SSD1306:

    # TODO: SPI Mode, horizontal and vertical addressing
    # I2C device address
    DEFAULT_ADDRESS = const(0x3C)
    # Screen size
    WIDTH = const(128)
    HEIGHT = const(64)
    # Empty and filled pixels
    BLACK = const(0x00)
    WHITE = const(0x01)
    # Setup and setting commands
    DISPLAY_ON = const(0xAF)
    DISPLAY_OFF = const(0xAE)
    # Select contrast, contrast value from const(0x00) to const(0xFF) should follow
    SELECT_CONTRAST = const(0x81)
    # RAM content usage for displaying
    USE_RAM_CONTENT = const(0xA4)
    IGNORE_RAM_CONTENT = const(0xA5)
    # Display inversion
    DISPLAY_INVERT_OFF = const(0xA6)
    DISPLAY_INVERT_ON = const(0xA7)
    # Column addressing
    LOWER_NIBBLE = const(0x00) # up to const(0x0f)
    HIGHER_NIBBLE = const(0x00) # up to const(0x0f)
    LOWER_NIBBLE_CMD = const(0x00 + LOWER_NIBBLE)
    HIGHER_NIBBLE_CMD = const(0x10 + HIGHER_NIBBLE)
    # Addressing mode
    SELECT_ADDRESSING = const(0x20)
    HORIZONTAL_ADDRESSING = const(0x00) # Not implemented yet
    VERTICAL_ADDRESSING = const(0x01) # Not implemented yet
    PAGE_ADDRESSING = const(0x10)
    # Start RAM page
    INITIAL_RAM_PAGE = const(0x00) # 0-7
    INITIAL_RAM_PAGE_CMD = const(0xB0 + INITIAL_RAM_PAGE)
    # Display start line
    START_LINE = const(0x00) # up to const(0x3F)
    START_LINE_CMD = const(0x40 + START_LINE)
    # Segment re-map
    SET_REMAP_OFF = const(0xA0)
    SET_REMAP_ON = const(0xA1)
    # MUX, must be followed by MUX ratio (up to 3F)
    SELECT_MULTIPLEX_RATIO = const(0xA8)
    # COM output scan mode
    COM_SCAN_NORMAL = const(0xC0)
    COM_SCAN_REMAP = const(0xC8)
    # Display offset, must be followed by offset (up to 3E)
    SELECT_DISPLAY_OFFSET = const(0xD3)
    # COM pins hw configuration
    SELECT_COM_PINS = const(0xDA)
    COM_PINS_SEQUENTIAL_NO_REMAP = const(0x02) 
    COM_PINS_SEQUENTIAL_REMAP = const(0x22)
    COM_PINS_ALTERNATIVE_NO_REMAP = const(0x32)
    COM_PINS_ALTERNATIVE_REMAP = const(0x12)
    # Oscillator divider and frequency
    SELECT_OSCILLATOR = const(0xD5)
    OSC_FREQUENCY = const(0x80) # const(0x00), const(0x10), const(0x20), ... const(0xF0)
    OSC_DIVIDER = const(0x00) # const(0x00) to const(0x0F)
    OSC_SETTINGS = const(OSC_FREQUENCY + OSC_DIVIDER)
    # Pre-charge period
    SELECT_PRECHARGE = const(0xD9)
    PRECHARGE_PHASE_1 = const(0x20) # const(0x10), const(0x20), ... const(0xF0)
    PRECHARGE_PHASE_2 = const(0x02) # const(0x01) to const(0x0F)
    PRECHARGE_SETTING = const(PRECHARGE_PHASE_1 + PRECHARGE_PHASE_2)
    # Vcomh deselect level
    SELECT_VCOMH_DESELECT = const(0xDB)
    VCOMH_65 = const(0x00) # 0.65xVcc
    VCOMH_77 = const(0x20) # 0.77xVcc
    VCOMH_83 = const(0x30) # 0.83xVcc
    # Charge pump
    SELECT_CHARGE_PUMP = const(0x8D)
    CHARGE_PUMP_ON = const(0x14)

    def _send_byte(self, byte):
        self.bus.writeto(self.address, bytearray([byte]))

    def _turn_off(self):
        self._send_byte(self.DISPLAY_OFF)

    def _turn_on(self):
        self._send_byte(self.DISPLAY_ON)

    def _configure_screen(self):
        self._turn_off()
        self._send_byte(self.SELECT_ADDRESSING)
        self._send_byte(self.PAGE_ADDRESSING)
        self._send_byte(self.INITIAL_RAM_PAGE_CMD)
        self._send_byte(self.COM_SCAN_REMAP)
        self._send_byte(self.LOWER_NIBBLE_CMD)
        self._send_byte(self.HIGHER_NIBBLE_CMD)
        self._send_byte(self.START_LINE_CMD)
        self._send_byte(self.SELECT_CONTRAST)
        self._send_byte(0xCF)
        self._send_byte(self.SET_REMAP_ON)
        self._send_byte(self.DISPLAY_INVERT_OFF)
        self._send_byte(self.SELECT_MULTIPLEX_RATIO)
        self._send_byte(0x3F)
        self._send_byte(self.SELECT_DISPLAY_OFFSET)
        self._send_byte(0x00)
        self._send_byte(self.SELECT_OSCILLATOR)
        self._send_byte(self.OSC_SETTINGS)
        self._send_byte(self.SELECT_PRECHARGE)
        self._send_byte(self.PRECHARGE_SETTING)
        self._send_byte(self.SELECT_COM_PINS)
        self._send_byte(self.COM_PINS_ALTERNATIVE_REMAP)
        self._send_byte(self.SELECT_VCOMH_DESELECT)
        self._send_byte(self.VCOMH_77)
        self._send_byte(self.SELECT_CHARGE_PUMP)
        self._send_byte(self.CHARGE_PUMP_ON)
        self._send_byte(self.USE_RAM_CONTENT)
        self._send_byte(self.DISPLAY_ON)
        self._turn_on()

    def update_screen(self):
        for i in range(8):
            self._send_byte(self.INITIAL_RAM_PAGE_CMD + i)
            self._send_byte(self.LOWER_NIBBLE_CMD)
            self._send_byte(self.HIGHER_NIBBLE_CMD)
            mv = memoryview(self.buffer)
            self.bus.writeto_mem(self.address, self.START_LINE_CMD, mv[(self.max_x * i):(self.max_x * (i+1))])

    def fill(self, color = WHITE):
        for i in range(len(self.buffer)):
            self.buffer[i] = 0 if color == self.WHITE else 0xFF

    def __init__(self, name, i2c_bus, address=DEFAULT_ADDRESS, width=WIDTH, height=HEIGHT):
        self.name = name
        self.bus = i2c_bus
        self.address = address
        self.current_x = 0
        self.current_y = 0
        self.current_cursor = 0
        self.max_x = width
        self.max_y = height
        self.buffer = bytearray(height * width // 8)
        self._configure_screen()
        self.fill(self.BLACK)
        self.update_screen()

    def draw_pixel(self, x, y, color):
        if (x >= self.max_x or y >= self.max_y):
            return
        if color == self.WHITE:
            self.buffer[x + (y / 8) * self.max_x] |= 1 << (y % 8)
        else:
            self.buffer[x + (y / 8) * self.max_x] &= ~(1 << (y % 8))

    def write_symbol_simple(self, symbol, font = fonts.FONT7X10):
        if(self.current_cursor + font[1] >= len(self.buffer)):
            return
        if symbol not in font[2].keys():
            symbol = "?"
        symboldata = font[2][symbol]
        for i in range(font[1]):
            self.buffer[self.current_cursor + i] = symboldata[i]
        self.current_cursor += font[1]
    
    def write_string_simple(self, string, font = fonts.FONT7X10):
        for s in string:
            self.write_symbol_simple(s, font)

    def set_symbol_cursor(self, position):
        if position >= len(self.buffer):
            return
        self.current_cursor = position
