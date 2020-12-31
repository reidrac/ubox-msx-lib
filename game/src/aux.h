#ifndef _AUX_H
#define _AUX_H

#include <stdint.h>

/**
 * Auxiliary functions.
 */

void put_text(uint8_t x, uint8_t y, const uint8_t *text);
void wait_for(uint8_t frames);

#endif // _AUX_H