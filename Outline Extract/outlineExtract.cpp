#include "outlineExtract.h"


//面积统计法求圆形有效区域的圆心位置和半径
void areaStatisticsMethod(Mat imgOrg, Point2i& center, int& radius, int threshold)
{
	Mat src = imgOrg.clone();//复制原图，以避免修改原图
	
	//imwrite("area_src.tiff", src);//保存图片供论文使用

	Size srcSize = src.size();//获得原始图像的尺寸

	Mat gray,binarized;

	cvtColor(src, gray, CV_BGR2GRAY);//对彩色原图进行灰度化

	cv::threshold(gray, binarized, threshold, 255, THRESH_BINARY);//以一定的阈值对灰度图像二值化

	/*imwrite("area_gray.tiff", gray);
	imwrite("area_binary.tiff", binarized);
	imshow("gray", gray);
	imshow("binary", binarized);
	waitKey();*/
	
	//由于鱼眼图像圆形有效区域的像素亮度较高，所以二值化后会变成白色区域，
	//我们可以把这个白色区域看作是平面几何图像，从而求取它的重心坐标，作为圆心坐标
	//而一般圆形有效区域中暗点较少，所以可以把白色区域的面近似为圆形有效区域的面积，
	//从而求得半径大小
	
	double area = 0.0;
	int xTorque=0, yTorque=0;
	for (int j = 0; j < srcSize.height; j++)
	{
		for (int i = 0; i < srcSize.width; i++)
		{
			if (binarized.at<uchar>(Point(i, j)) == 255)
			{
				area++;//统计出白色区域的像素点个数，作为白色区域的面积

				//计算x、y两个坐标方向上的一次矩
				xTorque += i;
				yTorque += j;
			}
		}
	}
	radius = sqrt(area / PI);//求得圆形有效区域的半径

	//求得白色区域的重点位置作为圆形有效区域的圆心
	center.x = xTorque / area;
	center.y = yTorque / area;

#ifdef _DEBUG_
	cout << "Use the Area Statistics Method:" << endl
		<< "\tThe center is (" << center.x << ", "
		<< center.y << ")" << endl
		<< "\tThe radius is " << radius << endl;

	circle(src, center, radius, Scalar(0, 0, 255), 2);
	circle(src, center, 3, Scalar(0, 0, 255), -1);

	namedWindow("Area Statistics Method Result", CV_WINDOW_AUTOSIZE);
	imshow("Area Statistics Method Result", src);
	imwrite("area_ret.tiff", src);
	waitKey();

#endif
}
//传统线扫描法
void ScanLineMethod(Mat imgOrg, Point2i& center, int& radius, int threshold, Point offsetCenter, int adjustRadius)
{
	Mat src, gray,gray_back;
	src = imgOrg.clone();

	//imwrite("Scan_src.tiff", src);

	cvtColor(src, gray, CV_BGR2GRAY);
	gray_back = gray.clone();

	int left, right, top, bottom;


	double minVal, maxVal;
	Point2i minLoc, maxLoc;

	uchar count = 0;
	for (int i = 0; i < gray.rows; i++)
	{
		minMaxLoc(gray.row(i), &minVal, &maxVal, &minLoc, &maxLoc);
		if ((maxVal - minVal)>threshold)
		{
			maxLoc.y = i;
			gray_back.row(i) = 255;
			gray_back.row(i-1) = 255;
			
			//circle(src, maxLoc, 3, Scalar(0, 255, 255), -1);

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
			maxLoc.y = i;
			gray_back.row(i) = 255;
			gray_back.row(i + 1) = 255;

			//circle(src, maxLoc, 3, Scalar(0, 255 , 255), -1);

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
			maxLoc.x = i;
			gray_back.col(i) = 255;
			gray_back.col(i - 1) = 255;

			//circle(src, maxLoc, 3, Scalar(0, 255, 255), -1);

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
			maxLoc.x = i;
			gray_back.col(i) = 255;
			gray_back.col(i + 1) = 255;

			//circle(src, maxLoc, 3, Scalar(0, 255, 255), -1);

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
	imwrite("Scan_gray.tiff", gray_back);
	cout << "Use the ScanLine Method:" << endl
		<< "\tThe center is (" << center.x << ", " 
		<< center.y << ")" << endl
		<< "\tThe radius is " << radius << endl;

	circle(src, center, radius, Scalar(0, 0, 255), 2);
	circle(src, center, 3, Scalar(0, 0, 255), -1);
	imwrite("Scan_ret.tiff", src);

	namedWindow("ScanLine Method Result", CV_WINDOW_AUTOSIZE);
	imshow("ScanLine Method Result", src);
	waitKey();
#endif

}
//霍夫圆变换法
void HoughCircleMethod(Mat imgOrg, Point2i& center, int& radius)
{
	Mat src, gray;
	src = imgOrg.clone();//复制原图，防止函数内部对其更改

	//imwrite("Hough_src.tiff", src);//保存原始供论文使用

	cvtColor(src, gray, CV_BGR2GRAY);//对原始图像灰度化

	//imwrite("Hough_gray.tiff", gray);

	GaussianBlur(gray, gray, Size(9, 9), 2, 2);//使用高斯滤波，减小噪声影响

	//使用霍夫圆检测法，检测图形中的圆形轮廓
	vector<Vec3f> circles;
	HoughCircles(gray, circles, CV_HOUGH_GRADIENT, 1, gray.rows / 4, 180,90,gray.rows/6);

	//将检测出的圆形轮廓在原图上一一标示出来
	for (size_t i = 0; i < circles.size(); i++)
	{
		Point center(cvRound(circles[i][0]), cvRound(circles[i][1]));
		int radius = cvRound(circles[i][2]);
		// circle center
		cv::circle(src, center, 3, Scalar(0, 0, 255), -1, 8, 0);
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
	imwrite("Hough_ret.tiff", src);
	waitKey();
#endif

}

//变角度线扫描法——改进后的线扫描法
void revisedScanLineMethod(Mat imgOrg, Point2i& center, int& radius, int threshold, int N)
{
	Mat src, gray;
	src = imgOrg.clone();
	cvtColor(src, gray, CV_BGR2GRAY);

	vector<Point> points;
	vector<double> distance;

	Size imgSize = src.size();

	int x, y;
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
		int flag = 0;

		double minVal, maxVal;

		if (0 == n)
		{
			for (int i = 0; i < imgSize.height; i++)
			{
				minMaxLoc(gray.row(i), &minVal, &maxVal, &ptMin1, &ptMax1);
				if ((maxVal - minVal)>threshold)
				{
					flag++;

					ptMax1.y = i;
					//cout << "horizontal top:" << endl;
					//cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;
					points.push_back(ptMax1);
					goto top_label;
				}
			}
		top_label:

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 5, Scalar(0, 255, 255), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = imgSize.height - 1; i >= 0; i--)
			{
				minMaxLoc(gray.row(i), &minVal, &maxVal, &ptMin2, &ptMax2);
				if ((maxVal - minVal) > threshold)
				{
					flag++;

					ptMax2.y = i;
					//cout << "horizontal bottom:" << endl;
					//cout << "ptMax2=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;

					//src.row(i) = Scalar(0, 0, 255);
					//src.row(i + 1) = Scalar(0, 0, 255);

					points.push_back(ptMax2);
					goto bottom_label;
				}
			}
		bottom_label:

#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 5, Scalar(0, 255, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0), 2);
			imshow("src", src);
			waitKey();
#endif
			if (flag == 2)
			{
				distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));
			}
			else if (flag == 1)
			{
				points.pop_back();
			}
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
						flag++;
						//cout << "jump outer1" << endl;
						//cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;
						points.push_back(ptMax1);

						/*						Point start, end;
						for (int k = 0; k <= i; k++)
						{
						x = k;
						y = -tan(theta)*(x - i);
						if (k == 0)
						{
						start = Point(x, y);
						}
						else if (k == i)
						{
						end = Point(x, y);
						}


						}
						line(src, start, end, Scalar(0, 0, 255), 2);*/

						goto outer1;
					}
				}
			}
		outer1:

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 5, Scalar(0, 255, 255), -1);
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
						flag++;
						//cout << "jump outer2" << endl;
						//cout << "ptMax2=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;
						points.push_back(ptMax2);

						//Point start, end;
						//for (int k = i; k < imgSize.width; k++)
						//{
						//	x = k;
						//	y = imgSize.height - 1 - tan(theta)*(x - i);
						//	if (k == i)
						//	{
						//		start = Point(x, y);
						//	}
						//	else if (k == imgSize.width-1)
						//	{
						//		end = Point(x, y);
						//	}


						//}
						//line(src, start, end, Scalar(0, 0, 255), 2);

						goto outer2;
					}
				}
			}
		outer2:
			;

#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 5, Scalar(0, 255, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0), 2);
			imshow("src", src);
			waitKey();
#endif
			if (flag == 2)
			{
				distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));
			}
			else if (flag == 1)
			{
				points.pop_back();
			}

		}
		else if (N == n)
		{
			for (int i = 0; i < imgSize.width; i++)
			{
				minMaxLoc(gray.col(i), &minVal, &maxVal, &ptMin1, &ptMax1);
				if ((maxVal - minVal)>threshold)
				{
					flag++;
					ptMax1.x = i;
					//cout << "vertical left:" << endl;
					//cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;

					//src.col(i) = Scalar(0, 0, 255);
					//src.col(i - 1) = Scalar(0, 0, 255);
					points.push_back(ptMax1);
					goto left_label;
				}
			}
		left_label:

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 5, Scalar(0, 255, 255), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = gray.cols - 1; i >= 0; i--)
			{
				minMaxLoc(gray.col(i), &minVal, &maxVal, &ptMin2, &ptMax2);
				if ((maxVal - minVal) > threshold)
				{
					flag++;
					ptMax2.x = i;
					//cout << "vertical right:" << endl;
					//cout << "ptMax1=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;
					points.push_back(ptMax2);

					//src.col(i) = Scalar(0, 0, 255);
					//src.col(i + 1) = Scalar(0, 0, 255);

					goto right_label;
				}
			}

		right_label:

#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 5, Scalar(0, 255, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0), 2);
			imshow("src", src);
			waitKey();
#endif
			if (flag == 2)
			{
				distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));
			}
			else if (flag == 1)
			{
				points.pop_back();
			}

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
						flag++;
						//cout << "jump outer3" << endl;
						//cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;
						points.push_back(ptMax1);

						//Point start, end;
						//for (int k = 0; k <= i; k++)
						//{
						//	x = k;
						//	y = imgSize.height - 1 - tan(theta)*(x - i);

						//	if (k == 0)
						//	{
						//		start = Point(x, y);
						//	}
						//	else if (k == i)
						//	{
						//		end = Point(x, y);
						//	}
						//}
						//line(src, start, end, Scalar(0, 0, 255), 2);

						goto outer3;
					}
				}
			}
		outer3:

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 5, Scalar(0, 255, 255), -1);
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
						flag++;
						//cout << "jump outer4" << endl;
						//cout << "ptMax2=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;
						points.push_back(ptMax2);

						/*			Point start, end;
						for (int k = i; k < imgSize.width; k++)
						{
						x = k;
						y = -tan(theta)*(x - i);
						if (k == i)
						{
						start = Point(x, y);
						}
						else if (k == imgSize.width - 1)
						{
						end = Point(x, y);
						}


						}
						line(src, start, end, Scalar(0, 0, 255), 2);*/

						goto outer4;
					}
				}
			}
		outer4:

			;
#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 5, Scalar(0, 255, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0), 2);
			imshow("src", src);
			waitKey();
#endif
			if (flag == 2)
			{
				distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));
			}
			else if (flag == 1)
			{
				points.pop_back();
			}

		}
		else
		{
			cout << "The value of n is error!" << endl;
			break;
		}
	}


	//vector<Point>::iterator itero = points.begin();
	//ofstream of("points.txt", ios::trunc | ios::out);
	//while (itero != points.end())
	//{
	//	of << (*itero).x << ", " << (*itero).y << endl;
	//	itero++;
	//}
	//of.close(); 


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

	if (!CircleFitByKasa(validPoints, center, radius))
	{
		cout << "Revisied LineScan Method Failed, Because the Circle Fit Method failed!" << endl;
		return;
	}

//#ifdef _DEBUG_
	cout << "Use the Revised ScanLine Method:" << endl
		<< "\tThe center is (" << center.x << ", "
		<< center.y << ")" << endl
		<< "\tThe radius is " << radius << endl;

	circle(src, center, radius, Scalar(0, 0, 255), src.cols/300);
	circle(src, center, 5, Scalar(0, 255, 255), -1);

	//namedWindow("Revised ScanLine Method Result", CV_WINDOW_AUTOSIZE);
	//imshow("Revised ScanLine Method Result", src);
	extern const char window_name[];
	imshow(window_name, src);
	//imwrite("Revised_Scan_ret.tiff", src);
	//waitKey();
//#endif

}
//圆拟合函数，性能很好，但要防止拟合时出现奇异值的情况
bool CircleFitByKasa(vector<Point> validPoints, Point& center, int&	 radius)
{
	if (validPoints.size() <= 2)
	{
		cout << "The Circle fit failed, Because there is not enought validate points to use!" << endl;
		return false;
	}

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

	center.x = p1 / 2;
	center.y = p2 / 2;
	radius = sqrt((pow(p1, 2) + pow(p2, 2)) / 4 + p3);

	//cout << center.x << endl << center.y << endl << radius << endl;
	return true;
}
