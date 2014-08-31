#include "globalInclude.h"

#include "outlineExtract.h"
#include "latitudeCorrection.h"
#include "panoramaExpansion.h"


void Usage()
{
	cout << "extract <image-path> " << endl;
}


int main(int argc, char** argv)
{
	if (argc < 2)
	{
		Usage();
		return -1;
	}

	Mat imgOrg = imread(argv[1], CV_LOAD_IMAGE_COLOR);
	if (!imgOrg.data)
	{
		cout << "Failed to read in a image." << endl;
		return -1;
	}
	Point2i center;
	int radius = 0;

	//Extract the center and radius from the origin image
	//ScanLineMethod(imgOrg, center, radius, 125);
	revisedScanLineMethod(imgOrg, center, radius, 50 );
	//imshow("imgsrc", imgOrg);
	//HoughCircleMethod(imgOrg, center, radius);
	Mat img1, img2, img3;
	for (double r = PI / 20; r <= PI; r += PI / 20)
	{
		img1=panoramaExpansion(imgOrg.clone(), center, radius,r,Forward);
		if (img1.data)
		{
			imshow("ret", img1);
			waitKey(10);
			
		}
	}

	//User multiple method to correct the distorted image
	//img1=latitudeCorrection( imgOrg,  center,  radius,Forward);
	//for (double r = PI / 20; r <= PI; r += PI / 20)
	//{
	//	img2 = latitudeCorrection(imgOrg.clone(), center, radius,  r);
	//	//img2 = latitudeCorrection(imgOrg.clone(), center, radius, r,Forward);

	//	if (img2.data)
	//	{
	//		imshow("img2", img2);
	//		waitKey(5);
	//	}
	//	else
	//	{
	//		cout << "Failed to rectified!" << endl;
	//	}

	//}

	waitKey();
	return 0;
}