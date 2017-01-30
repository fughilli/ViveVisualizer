class OBJImporter(object):
    @staticmethod
    def triangulate(indices, flat=False):
        if(len(indices) < 3):
            raise Exception("Cannot triangulate less than 3 indices.")
        elif(len(indices) == 3):
            if flat:
                return indices
            else:
                return [indices]
        else:
            ret = []
            for i in range(1, len(indices) - 1):
                ret.append([indices[0]] + indices[i:i+2])

            if flat:
                return reduce(lambda a,b : a+b, ret)
            return ret

    @staticmethod
    def imp(filename, triangulate=True, flat=False):
        f = open(filename)

        ret = [[], []]

        def parseindex(i):
            if '//' in i:
                return int(i[:i.find('//')]) - 1
            return int(i) - 1

        for line in f.readlines():
            line = line.strip()
            parts = line.split()
            command = parts[0]
            parts = parts[1:]

            if(command == 'v'):
                if flat:
                    ret[0].extend([float(x) for x in parts])
                else:
                    ret[0].append([float(x) for x in parts])
            if(command == 'f'):
                ret[1].extend(OBJImporter.triangulate([parseindex(x) for x in parts], flat=flat))

        return ret
