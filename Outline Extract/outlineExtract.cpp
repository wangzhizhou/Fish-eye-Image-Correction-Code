#include "outlineExtract.h"

void revisedScanLineMethod(Mat imgOrg, Point2i& center, int& radius, int threshold, Point offsetCenter, int adjustRadius)
{
	Mat src, gray;
	src = imgOrg.clone();
	//src = imgOrg;
	cvtColor(src, gray, CV_BGR2GRAY);

	vector<Point> points;
	vector<double> distance;


	//circle(src, center, 3, Scalar(0, 0, 255), -1);
	//circle(src, center, radius, Scalar(255, 255, 255)); 

	Size imgSize = src.size();

	int x, y;
	const int N = 10;
	double theta = 0;

	for (int n = 0; n < 2 * N; n++, theta = PI*n / (2 * N))
	{
		int min1, min2;
		min1 = min2 = 255;
		int max1, max2;
		max1 = max2 = 0;
		int radius = 0;
		Point ptMax1(0, 0), ptMax2(0, 0);
		Point ptMin1(0, 0), ptMin2(0, 0);

		double minVal, maxVal;

		if (0 == n)
		{
			for (int i = 0; i < imgSize.height; i++)
			{
				minMaxLoc(gray.row(i), &minVal, &maxVal, &ptMin1, &ptMax1);
				if ((maxVal - minVal)>threshold)
				{
					ptMax1.y = i;
					cout << "horizontal top:" << endl;
					cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;
					points.push_back(ptMax1);
					break;
				}
			}
#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 3, Scalar(0, 192, 255), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = imgSize.height - 1; i >= 0; i--)
			{
				minMaxLoc(gray.row(i), &minVal, &maxVal, &ptMin2, &ptMax2);
				if ((maxVal - minVal) > threshold)
				{
					ptMax2.y = i;
					cout << "horizontal bottom:" << endl;
					cout << "ptMax2=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;

					points.push_back(ptMax2);
					break;
				}
			}
#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 3, Scalar(0, 0, 192), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0));
			imshow("src", src);
			waitKey();
#endif
			distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));
		}
		else if (0 < n&&n < N)
		{


			for (int i = 0; i < imgSize.width; i++)
			{
				for (int j = 0; j <= i; j++)
				{
					x = j;
					y = -tan(theta)*(x - i);

					Point ptCur(x, y);
					if (!ptCur.inside(Rect(0, 0, imgSize.width, imgSize.height)))
					{
						continue;
					}

					uchar I = gray.at<uchar>(ptCur);

					if (I > max1)
					{
						max1 = I;
						ptMax1 = ptCur;
					}
					if (I < min1)
					{
						min1 = I;
					}

					if (abs(max1 - min1)>threshold)
					{
						cout << "jump outer1" << endl;
						cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;
						points.push_back(ptMax1);
						goto outer1;
					}
				}
			}
		outer1:

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 3, Scalar(0, 255, 255), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = imgSize.width - 1; i >= 0; i--)
			{
				for (int j = i; j < imgSize.width; j++)
				{
					x = j;
					y = imgSize.height - 1 - tan(theta)*(x - i);

					Point ptCur(x, y);

					if (!ptCur.inside(Rect(0, 0, imgSize.width, imgSize.height)))
					{
						continue;
					}
					uchar I = gray.at<uchar>(ptCur);

					if (I > max2)
					{
						max2 = I;
						ptMax2 = ptCur;
					}
					if (I < min2)
					{
						min2 = I;
					}

					if (abs(max2 - min2)>threshold)
					{
						cout << "jump outer2" << endl;
						cout << "ptMax2=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;
						points.push_back(ptMax2);
						goto outer2;
					}
				}
			}
		outer2:
			;

#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 3, Scalar(0, 0, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0));
			imshow("src", src);
			waitKey();	
#endif
			distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));

		}
		else if (N == n)
		{
			for (int i = 0; i < imgSize.width; i++)
			{
				minMaxLoc(gray.col(i), &minVal, &maxVal, &ptMin1, &ptMax1);
				if ((maxVal - minVal)>threshold)
				{
					ptMax1.x = i;
					cout << "vertical left:" << endl;
					cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;

					points.push_back(ptMax1);
					break;
				}
			}

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 3, Scalar(0, 255, 64), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = gray.cols - 1; i >= 0; i--)
			{
				minMaxLoc(gray.col(i), &minVal, &maxVal, &ptMin2, &ptMax2);
				if ((maxVal - minVal) > threshold)
				{
					ptMax2.x = i;
					cout << "vertical right:" << endl;
					cout << "ptMax1=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;

					points.push_back(ptMax2);
					break;
				}
			}

#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 3, Scalar(255, 0, 0), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0));
			imshow("src", src);
			waitKey();
#endif
			distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));

		}
		else if (N < n&&n < 2 * N)
		{
			for (int i = 0; i < imgSize.width; i++)
			{
				for (int j = 0; j <= i; j++)
				{
					x = j;
					y = imgSize.height - 1 - tan(theta)*(x - i);

					Point ptCur(x, y);
					if (!ptCur.inside(Rect(0, 0, imgSize.width, imgSize.height)))
					{
						continue;
					}
					uchar i = gray.at<uchar>(ptCur);

					if (i > max1)
					{
						max1 = i;
						ptMax1 = ptCur;
					}
					if (i < min1)
					{
						min1 = i;
					}

					if (abs(max1 - min1)>threshold)
					{
						cout << "jump outer3" << endl;
						cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;
						points.push_back(ptMax1);
						goto outer3;
					}
				}
			}
		outer3:
#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 3, Scalar(255, 255, 255), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = imgSize.width - 1 / 2; i >= 0; i--)
			{
				for (int j = i; j < imgSize.width; j++)
				{
					x = j;
					y = -tan(theta)*(x - i);

					Point ptCur(x, y);
					if (!ptCur.inside(Rect(0, 0, imgSize.width, imgSize.height)))
					{
						continue;
					}
					uchar I = gray.at<uchar>(ptCur);

					if (I > max2)
					{
						max2 = I;
						ptMax2 = ptCur;
					}
					if (I < min2)
					{
						min2 = I;
					}

					if (abs(max2 - min2)>threshold)
					{
						cout << "jump outer4" << endl;
						cout << "ptMax2=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;
						points.push_back(ptMax2);
						goto outer4;
					}
				}
			}
		outer4:

			;
#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 3, Scalar(255, 0, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 192));
			imshow("src", src);
			waitKey();
#endif
			distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));

		}
		else
		{
			cout << "The value of n is error!" << endl;
			break;
		}
	}

	//find out validate points
	double mean = 0;
	vector<double>::iterator iter = distance.begin();
	while (iter != distance.end())
	{
		mean += *iter;
		iter++;
	}
	mean /= distance.size();

	vector<Point> validPoints;
	for (int i = 0; i < distance.size(); i++)
	{
		if (distance.at(i) < mean)
		{
			validPoints.push_back(points.at(2 * i));
			validPoints.push_back(points.at(2 * i + 1));
		}
	}

	//figure out the center and radius of the circle with Kasa method

	CircleFitByKasa(validPoints, center, radius);

#ifdef _DEBUG_
	cout << "Use the Revised ScanLine Method:" << endl
		<< "\tThe center is (" << center.x << ", "
		<< center.y << ")" << endl
		<< "\tThe radius is " << radius << endl;

	circle(src, center, radius, Scalar(0, 0, 255), 1);
	circle(src, center, 3, Scalar(0, 255, 255), -1);

	namedWindow("Revised ScanLine Method Result", CV_WINDOW_AUTOSIZE);
	imshow("Revised ScanLine Method Result", src);
	waitKey();
#endif

}
void CircleFitByKasa(vector<Point> validPoints, Point& center, int&	 radius)
{
	vector<Point3i> extendA;
	vector<int> extendB;
	vector<Point>::iterator iter = validPoints.begin();
	while (iter != validPoints.end())
	{
		extendA.push_back(Point3i((*iter).x, (*iter).y, 1));
		extendB.push_back((pow((*iter).x, 2) + pow((*iter).y, 2)));
		iter++;
	}
	Mat A = Mat(extendA).reshape(1);
	Mat	B = Mat(extendB).reshape(1);

	Mat_<double> dA, dB;
	Mat_<double> P(3, 1, CV_64F);
	A.convertTo(dA, CV_64F);
	B.convertTo(dB, CV_64F);
	P = dA.inv(CV_SVD)*dB;

	//cout << P << endl;

	double p1, p2, p3;
	p1 = P.at<double>(0, 0);
	p2 = P.at<double>(1, 0);
	p3 = P.at<double>(2, 0);

	center.x = p1/2;
	center.y = p2/2;
	radius = sqrt((pow(p1,2)+pow(p2,2))/4+p3);

	//cout << center.x << endl << center.y << endl << radius << endl;


}
void ScanLineMethod(Mat imgOrg, Point2i& center, int& radius, int threshold, Point offsetCenter, int adjustRadius)
{
	Mat src, gray;
	src = imgOrg.clone();
	cvtColor(src, gray, CV_BGR2GRAY);

	//GaussianBlur(gray, gray, Size(9, 9), 2, 2);

	int left, right, top, bottom;


	double minVal, maxVal;
	Point2i minLoc, maxLoc;

	uchar count = 0;
	for (int i = 0; i < gray.rows; i++)
	{
		minMaxLoc(gray.row(i), &minVal, &maxVal, &minLoc, &maxLoc);
		if ((maxVal - minVal)>threshold)
		{
			top = i;
			count++;
			break;
		}
	}
	for (int i = gray.rows - 1; i >= 0; i--)
	{
		minMaxLoc(gray.row(i), &minVal, &maxVal, &minLoc, &maxLoc);
		if ((maxVal - minVal) > threshold)
		{
			bottom = i;
			count++;
			break;
		}
	}
	for (int i = 0; i < gray.cols; i++)
	{
		minMaxLoc(gray.col(i), &minVal, &maxVal, &minLoc, &maxLoc);
		if ((maxVal - minVal)>threshold)
		{
			left = i;
			count++;
			break;
		}
	}
	for (int i = gray.cols - 1; i >= 0; i--)
	{
		minMaxLoc(gray.col(i), &minVal, &maxVal, &minLoc, &maxLoc);
		if ((maxVal - minVal) > threshold)
		{
			right = i;
			count++;
			break;
		}
	}
	if (4 != count)
	{
		std::cout << "The ScanLine Method Failed!" << endl
			<< "Tip: " << endl
			<< "\tyou can try to adjust " << endl
			<< "\tthe value of threshold to make it work." << endl
			<< "\tcurrent value of threshold is: " << threshold << endl;
		return;
	}
	//rectangle(src, Point(left, top), Point(right, bottom), Scalar(0, 0, 255),2);

	center.x = (right + left) / 2 + offsetCenter.x;
	center.y = (top + bottom) / 2 + offsetCenter.y;

	double radius_max = max(right - left, bottom - top) / 2;
	double radius_min = min(right - left, bottom - top) / 2;
	double radius_avg = (radius_max + radius_min) / 2;

	radius = radius_max + adjustRadius;

#ifdef _DEBUG_
	cout << "Use the ScanLine Method:" << endl
		<< "\tThe center is (" << center.x << ", " 
		<< center.y << ")" << endl
		<< "\tThe radius is " << radius << endl;

	circle(src, center, radius, Scalar(0, 0, 255), 2);
	circle(src, center, 3, Scalar(0, 255, 255), -1);

	namedWindow("ScanLine Method Result", CV_WINDOW_AUTOSIZE);
	imshow("ScanLine Method Result", src);
	waitKey();
#endif

}

void HoughCircleMethod(Mat imgOrg, Point2i& center, int& radius)
{
	Mat src, gray;
	src = imgOrg.clone();

	cvtColor(src, gray, CV_BGR2GRAY);
	GaussianBlur(gray, gray, Size(9, 9), 2, 2);

	vector<Vec3f> circles;
	HoughCircles(gray, circles, CV_HOUGH_GRADIENT, 1, gray.rows / 8, 200, 100, 0, 0);

	for (size_t i = 0; i < circles.size(); i++)
	{
		Point center(cvRound(circles[i][0]), cvRound(circles[i][1]));
		int radius = cvRound(circles[i][2]);
		// circle center
		cv::circle(src, center, 3, Scalar(0, 255, 0), -1, 8, 0);
		// circle outline
		cv::circle(src, center, radius, Scalar(0, 0, 255), 2, 8, 0);
	}

	/// Show your results
	if (circles.size())
	{
		center.x = circles[0][0];
		center.y = circles[0][1];
		radius = circles[0][2];
	}

#ifdef _DEBUG_
	cout << "Use the HoughCircle Method:" << endl
		<< "\tThe center is (" << center.x << ", "
		<< center.y << ")" << endl
		<< "\tThe radius is " << radius << endl;

	namedWindow("Hough Circle Transform Result", CV_WINDOW_AUTOSIZE);
	imshow("Hough Circle Transform Result", src);
	waitKey();
#endif

}

