#pragma once
#include "globalInclude.h"
#include "tools.h"
#include "findCircleParameter.h"

class corrector
{
private:
	corrector();
	~corrector();
public:
	static void dispHeaveAndEarthCorrectImage(Mat sourceImage);
private:
	static Mat heavenAndEarthCorrect(Mat imgOrg, Point center, int radius, double startRadian = 0, CorrectType type = Reverse);

};