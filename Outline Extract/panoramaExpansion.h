#include "globalInclude.h"

//The method only suitable for the fish-eye image which been taken vertically

Mat panoramaExpansion(Mat imgOrg, Point center, int radius, double startRadian = 0,CorrectType type = Reverse);