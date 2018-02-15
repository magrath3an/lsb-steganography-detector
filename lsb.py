"""Requires some external modules."""
from PIL import Image
import numpy as np
import math, os
import argparse

w = 0
h = 0

class SamplePairsAnalysis():
    """Sample Pairs Analysis attack on LSB steganography."""

    def input_file(self, image):
        """Split file into colour bands."""
        global w, h
        img = Image.open(image)
        w, h = img.size
        # check if image is RGB
        if len(img.split()) != 3:
            return False
        else:
            # split into colour bands
            r, g, b = img.split()
            # turn into arrays
            red = r.load()
            green = g.load()
            blue = b.load()
            return red, green, blue

    def analyse_file(self, array):
        """RS sample pairs analysis attack."""
        P = []
        for i in range(w):
            for j in range(h - 1):
                P.append((array[i, j], array[i, j+1]))
        # primary sets
        x = 0
        y = 0
        K = 0
        for k in range(len(P)):
            # (r,s) = kth pair of P
            r, s = P[k]
            # natural image cardinalities of x and y should be the same
            if (s % 2 == 0 and r < s) or (s % 2 != 0 and r > s):
                x += 1
            elif (s % 2 == 0 and r > s) or (s % 2 != 0 and r < s):
                y += 1
            elif math.floor(r/2) == math.floor(s/2):
                # K is the number of pixel pairs where both values belong to the same LSB pair W U Z
                K += 1
        # K will only be zero with an extremely low probability in natural images
        if K == 0:
            print("[!] SPA failed becuase K = 0")
            exit(1)
        a = 2 * K
        b = 2 * (2 * x - w * (h - 1))
        c = y - x
        D = math.pow(b, 2) - (4 * a * c)
        if a > 0:
            p1 = (-b + math.sqrt(D)) / (2 * a)
            p2 = (-b - math.sqrt(D)) / (2 * a)
        else:
            p1 = -1
            p2 = -1
        # from initial testing 0.025 seems to be a good value to detect stego content
        return min(p1, p2).real

    def output(self, image):
        """Provide output of the attack."""
        if self.input_file(image) == False:
            print("[!] Image not correctly formatted, might have an alpha channel")
        else:
            r, g, b = self.input_file(image)
            if self.analyse_file(r) > 0.025:
                print("[+] {} contains steganographic content in the Red plane".format(image))
                print("Estimated change-rate = {}".format(self.analyse_file(r)))
                print("Estimated embedded message in bpp = {}".format(("%.2f" % (2 * self.analyse_file(r)))))
            if self.analyse_file(g) > 0.025:
                print("[+] {} contains steganographic content in the Green plane".format(image))
                print("Estimated change-rate = {}".format(self.analyse_file(g)))
                print("Estimated embedded message in bpp = {}".format(("%.2f" % (2 * self.analyse_file(g)))))
            if self.analyse_file(b) > 0.025:
                print("[+] {} contains steganographic content in the Blue plane".format(image))
                print("Estimated change-rate = {}".format(self.analyse_file(b)))
                print("Estimated embedded message in bpp = {}".format(("%.2f" % (2 * self.analyse_file(b)))))
            elif self.analyse_file(r) < 0.025 and self.analyse_file(g) < 0.025 and self.analyse_file(b) < 0.025:
                print("{} is likely natural, i.e. no steganographic content".format(image))


class VisualAttack():
    """For retrieveal of LSB components"""

    def input_file(self, filename):
        """Generate pixel map from image file."""
        img = Image.open(filename)
        w, h = img.size[0], img.size[1]
        rsize = img.resize((w, h))
        pixel_map = np.asarray(rsize)
        pixel_map.flags.writeable = True
        return pixel_map

    def analyse_file(self, x, pixel_map):
        """Enhance a given bitplane (x)."""
        for i in range(len(pixel_map)):
            for j in range(len(pixel_map[i])):
                for k in range(len(pixel_map[i][j])):
                    # convert int to bits
                    bits = '{:08b}'.format(pixel_map[i][j][k])
                    # enhance at that level
                    if int(bits[x]) == 0:
                        continue
                    elif int(bits[x]) == 1:
                        pixel_map[i][j][k] = 255
        # return modified pixel map
        return pixel_map


def parse_args():
    """Provide arguments for the script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-va", help="perform a 'Visual Attack' on a given image to extract bitplanes")
    parser.add_argument("-spa", help="perform statistical attack on a given image to determine if file contains embedded content")
    args = parser.parse_args()
    return args


def main():
    """Main entry point into the script."""
    args = parse_args()
    if args.va:
        attack = VisualAttack()
        pixel_map = attack.input_file(args.va)
        for i in range(8):
            pixel_map_analysis = attack.analyse_file(i, pixel_map)
            output = Image.fromarray(pixel_map_analysis)
            output.save("output_bitplane({}).png".format(i + 1))
            print("[+] output_bitplane({}).png saved to the current directory".format(i + 1))
    elif args.spa:
        attack = SamplePairsAnalysis()
        attack.output(args.spa)

if __name__ == '__main__':
    main()
